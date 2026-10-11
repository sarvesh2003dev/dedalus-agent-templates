"""Deploy one CSV/SQLite worker and verify its data across a real sleep/wake cycle."""

import argparse
import base64
import getpass
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SQL = "SELECT region, SUM(amount_cents) AS total_cents FROM sales GROUP BY region ORDER BY region"
EXPECTED = {"columns": ["region", "total_cents"],
            "rows": [["APAC", 210000], ["EU", 260000], ["US", 320000]]}
TERMINAL = {"succeeded", "failed", "cancelled", "expired"}

# UTF-8 JSON over stdin avoids binary-stdin and nested-archive path problems.
UPLOAD = """import base64, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=False)
files = json.load(sys.stdin)
if set(files) != {'agent.py', 'sample-sales.csv'}:
    raise ValueError('Unexpected deployment files')
for name, content in files.items():
    (root / name).write_bytes(base64.b64decode(content, validate=True))
print('Uploaded agent.py and sample-sales.csv')
"""


class DemoError(RuntimeError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def save_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def payload():
    return json.dumps({name: base64.b64encode((ROOT / "data-agent" / name).read_bytes()).decode("ascii")
                       for name in ("agent.py", "sample-sales.csv")})


def assert_preserved(before, after, before_query, after_query, proof_token):
    if before.get("proof_token") != proof_token or after.get("proof_token") != proof_token:
        raise DemoError("The unique proof token was not recovered.")
    if before.get("row_count") != 6 or before.get("source_sha256") != hashlib.sha256(
            (ROOT / "data-agent" / "sample-sales.csv").read_bytes()).hexdigest():
        raise DemoError("The loaded data does not match the bundled sample.")
    if before != after:
        raise DemoError("Saved database, rows or metadata changed across recovery.")
    if before_query != EXPECTED or after_query != EXPECTED:
        raise DemoError("The SQL query did not return the expected real aggregates.")


class Machines:
    def __init__(self, client, timeout_seconds=240, poll_seconds=1):
        self.client = client
        self.timeout_seconds = timeout_seconds
        self.poll_seconds = poll_seconds

    def wait_phase(self, machine_id, phase):
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            machine = self.client.machines.retrieve(machine_id=machine_id)
            current = machine.status.phase
            if current == phase:
                return
            if current in {"failed", "destroying", "destroyed"}:
                raise DemoError(f"Machine entered {current} while waiting for {phase}.")
            time.sleep(self.poll_seconds)
        raise DemoError(f"Timed out waiting for machine to become {phase}.")

    def execute(self, machine_id, command, stdin=None, timeout_ms=120000):
        arguments = {"machine_id": machine_id, "command": command, "timeout_ms": timeout_ms}
        if stdin is not None:
            arguments["stdin"] = stdin
        execution = self.client.machines.executions.create(**arguments)
        deadline = time.monotonic() + timeout_ms / 1000 + 60
        while execution.status not in TERMINAL:
            delay = max(self.poll_seconds, (execution.retry_after_ms or 0) / 1000)
            if time.monotonic() + delay >= deadline:
                self.client.machines.executions.delete(machine_id=machine_id,
                                                       execution_id=execution.execution_id)
                raise DemoError(f"Execution {execution.execution_id} exceeded its deadline.")
            time.sleep(delay)
            execution = self.client.machines.executions.retrieve(
                machine_id=machine_id, execution_id=execution.execution_id)
        output = self.client.machines.executions.output(
            machine_id=machine_id, execution_id=execution.execution_id)
        if execution.status != "succeeded" or execution.exit_code not in {None, 0}:
            # The key is held on the local client and is never sent to this worker.
            detail = (output.stderr or execution.error_message or "No diagnostics")[:2000]
            raise DemoError(f"Execution {execution.execution_id} {execution.status}: {detail}")
        if output.stdout_truncated:
            raise DemoError("Execution output was truncated; cannot verify it.")
        return output.stdout or ""

    def sleep(self, machine_id):
        if self.client.machines.retrieve(machine_id=machine_id).status.phase != "sleeping":
            self.client.machines.sleep(machine_id=machine_id)
        self.wait_phase(machine_id, "sleeping")

    def wake(self, machine_id):
        phase = self.client.machines.retrieve(machine_id=machine_id).status.phase
        if phase == "stopping":
            self.wait_phase(machine_id, "sleeping")
            phase = "sleeping"
        if phase == "sleeping":
            self.client.machines.wake(machine_id=machine_id)
        self.wait_phase(machine_id, "running")


def cloud_demo(client, report_path, machine_id=None, poll_seconds=1):
    run_id = uuid.uuid4().hex
    remote_dir = f"/home/machine/dedalus-data-demo/{run_id}"
    report = {"schema_version": 1, "mode": "dedalus_live", "status": "running",
              "run_id": run_id, "started_at": timestamp(), "remote_dir": remote_dir,
              "events": [], "live_sleep_wake_verified": False}
    api = Machines(client, poll_seconds=poll_seconds)
    acquired = False
    failure = None

    def event(stage):
        report["events"].append({"stage": stage, "at": timestamp()})
        save_report(report_path, report)
        print(stage, flush=True)

    def agent(*arguments):
        return json.loads(api.execute(machine_id, ["python3", remote_dir + "/agent.py",
                                                   "--state-dir", remote_dir + "/state",
                                                   *arguments]))

    save_report(report_path, report)
    try:
        if machine_id is None:
            event("Creating machine: 1 vCPU, 2 GiB RAM, 10 GiB disk; compute usage applies.")
            machine = client.machines.create(vcpu=1, memory_mib=2048, storage_gib=10,
                                             autosleep="5m", idempotency_key=run_id)
            machine_id = machine.machine_id
            report["created_machine"] = True
        else:
            # Fail before taking ownership if the ID cannot be retrieved.
            client.machines.retrieve(machine_id=machine_id)
            report["created_machine"] = False
        acquired = True
        report["machine_id"] = machine_id
        event(f"Machine recorded: {machine_id}")
        api.wake(machine_id)
        api.execute(machine_id, ["/bin/sh", "-c",
                                 "command -v python3 >/dev/null 2>&1 || "
                                 "(apt-get update -qq && DEBIAN_FRONTEND=noninteractive "
                                 "apt-get install -y python3)"], timeout_ms=180000)
        event("Uploading the worker and bundled sample CSV.")
        api.execute(machine_id, ["python3", "-c", UPLOAD, remote_dir], stdin=payload())
        report["before"] = agent("load", "--csv", remote_dir + "/sample-sales.csv",
                                  "--proof-token", run_id)
        report["query_before"] = agent("query", "--sql", SQL)
        assert_preserved(report["before"], report["before"], report["query_before"],
                         report["query_before"], run_id)
        event("Six real CSV rows saved; initial SQL totals verified.")
        api.sleep(machine_id)
        report["sleep_phase_observed"] = True
        event("Machine phase confirmed sleeping.")
        start = time.monotonic()
        api.wake(machine_id)
        report["wake_to_running_ms"] = round((time.monotonic() - start) * 1000, 2)
        report["after"] = agent("snapshot")
        report["query_after"] = agent("query", "--sql", SQL)
        report["wake_to_verified_data_ms"] = round((time.monotonic() - start) * 1000, 2)
        assert_preserved(report["before"], report["after"], report["query_before"],
                         report["query_after"], run_id)
        report["live_sleep_wake_verified"] = True
        event("Recovered the same proof token, database, rows and SQL totals after wake.")
    except (Exception, KeyboardInterrupt) as exc:
        failure = exc
        report["error_type"] = type(exc).__name__
    finally:
        if acquired:
            try:
                api.sleep(machine_id)
                report["final_machine_phase"] = "sleeping"
            except (Exception, KeyboardInterrupt) as exc:
                report["final_machine_phase"] = "unconfirmed"
                report["cleanup_error_type"] = type(exc).__name__
                if failure is None:
                    failure = DemoError("Verification finished, but final sleep was not confirmed. "
                                        "Check the machine in the Dedalus dashboard.")
        report["status"] = "passed" if failure is None else "failed"
        report["finished_at"] = timestamp()
        save_report(report_path, report)
        print(f"Report saved: {report_path.resolve()}", flush=True)
        if acquired:
            print(f"Final machine phase: {report['final_machine_phase']}. "
                  "Saved files remain on its disk.", flush=True)
    if failure is not None:
        raise failure
    return report


def local_demo(report_path):
    run_id = uuid.uuid4().hex
    state_dir = report_path.parent / ("local-state-" + run_id)

    def agent(*arguments):
        completed = subprocess.run([sys.executable, str(ROOT / "data-agent" / "agent.py"),
                                    "--state-dir", str(state_dir), *arguments],
                                   capture_output=True, text=True, check=True, timeout=30)
        return json.loads(completed.stdout)

    before = agent("load", "--csv", str(ROOT / "data-agent" / "sample-sales.csv"),
                   "--proof-token", run_id)
    before_query = agent("query", "--sql", SQL)
    # Every call runs a new Python process and reopens the database from disk.
    after = agent("snapshot")
    after_query = agent("query", "--sql", SQL)
    assert_preserved(before, after, before_query, after_query, run_id)
    report = {"schema_version": 1, "mode": "local_process_restart", "status": "passed",
              "live_sleep_wake_verified": False, "state_dir": str(state_dir.resolve()),
              "before": before, "after": after, "query_before": before_query,
              "query_after": after_query, "finished_at": timestamp()}
    save_report(report_path, report)
    print("PASS: real CSV, SQLite and fresh-process recovery. Cloud sleep/wake remains untested.")
    print(f"Report saved: {report_path.resolve()}")
    return report


def make_client(args):
    from dedalus_sdk import Dedalus

    key = os.environ.get("DEDALUS_API_KEY", "").strip()
    if args.prompt_key:
        key = getpass.getpass("Dedalus API key (hidden; not saved): ").strip()
    if not key:
        raise DemoError("Missing API key. Get Machines access at https://www.dedaluslabs.ai/ "
                        "then set DEDALUS_API_KEY locally or use --prompt-key.")
    # Mutations are not automatically repeated if a request times out.
    return Dedalus(api_key=key, timeout=30, max_retries=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    local = commands.add_parser("local-demo", help="Real disk persistence; no cloud account needed")
    local.add_argument("--report", type=Path)
    check = commands.add_parser("check-access", help="Read-only Machines API access check")
    check.add_argument("--prompt-key", action="store_true")
    demo = commands.add_parser("demo", help="Deploy, sleep, wake, verify, then leave machine sleeping")
    demo.add_argument("--prompt-key", action="store_true")
    choice = demo.add_mutually_exclusive_group(required=True)
    choice.add_argument("--create-machine", action="store_true", help="Create a machine; uses account credits")
    choice.add_argument("--machine-id", help="Use a dedicated test machine; this command will sleep it")
    demo.add_argument("--report", type=Path)
    args = parser.parse_args()
    report_path = getattr(args, "report", None) or ROOT / "runs" / (uuid.uuid4().hex + ".json")
    if report_path.exists():
        parser.error("The report path already exists. Choose a new path to preserve previous evidence.")
    try:
        if args.action == "local-demo":
            local_demo(report_path)
        else:
            with make_client(args) as client:
                if args.action == "check-access":
                    client.machines.list(limit=1)
                    print("Machines API access confirmed. No machine was created.")
                else:
                    cloud_demo(client, report_path, args.machine_id)
        return 0
    except KeyboardInterrupt:
        print("Interrupted. Check the saved report for the machine ID and final sleep status.", file=sys.stderr)
    except DemoError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
    except ImportError:
        print("Install the deployment dependency: python -m pip install -r requirements.txt", file=sys.stderr)
    except Exception as exc:
        code = getattr(exc, "status_code", None)
        detail = f" (HTTP {code})" if code is not None else ""
        print(f"ERROR: {type(exc).__name__}{detail}. Check access, network, and the saved run report.",
              file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
