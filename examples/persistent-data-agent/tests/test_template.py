"""Local persistence tests and SDK contract tests; these do not contact Dedalus."""

import contextlib
import importlib.util
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import httpx
from dedalus_sdk import Dedalus

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import deploy

spec = importlib.util.spec_from_file_location("data_worker", ROOT / "data-agent" / "agent.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def load(self):
        return worker.load_csv(self.root, ROOT / "data-agent" / "sample-sales.csv", "sales", "test-proof")

    def test_real_data_survives_fresh_processes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            report = deploy.local_demo(self.root / "proof.json")
        self.assertEqual(report["before"], report["after"])
        self.assertEqual(report["query_after"], deploy.EXPECTED)
        self.assertFalse(report["live_sleep_wake_verified"])

    def test_malformed_csv_is_rejected_without_fake_results(self):
        bad = self.root / "bad.csv"
        bad.write_text("region,amount\nUS,10,extra\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            worker.load_csv(self.root, bad, "sales", "test-proof")
        self.assertFalse((self.root / "datasets.sqlite3").exists())

    def test_missing_csv_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            worker.load_csv(self.root, self.root / "missing.csv", "sales", "test-proof")

    def test_duplicate_load_preserves_original_data(self):
        before = self.load()
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(before, worker.snapshot(self.root, "sales"))

    def test_read_only_query_cannot_delete_or_attach(self):
        before = self.load()
        for sql in ("DELETE FROM sales", "ATTACH DATABASE ':memory:' AS injected"):
            with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                worker.query(self.root, sql)
        self.assertEqual(before, worker.snapshot(self.root, "sales"))

    def test_empty_missing_database_does_not_get_created_by_query(self):
        with self.assertRaises(ValueError):
            worker.query(self.root, "SELECT 1")
        self.assertFalse((self.root / "datasets.sqlite3").exists())

    def test_invalid_identifiers_are_rejected(self):
        for name in ("../escape", 'x";DROP TABLE sales', "sqlite_master"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                worker.load_csv(self.root, ROOT / "data-agent" / "sample-sales.csv", name, "proof")

    def test_changed_rows_are_detected(self):
        before = self.load()
        with contextlib.closing(sqlite3.connect(self.root / "datasets.sqlite3")) as connection:
            with connection:
                connection.execute("UPDATE sales SET amount_cents = 0")
        after = worker.snapshot(self.root, "sales")
        with self.assertRaises(deploy.DemoError):
            deploy.assert_preserved(before, after, deploy.EXPECTED, deploy.EXPECTED, "test-proof")

    def test_cli_fails_before_cloud_creation_without_key(self):
        environment = dict(os.environ)
        environment.pop("DEDALUS_API_KEY", None)
        result = subprocess.run([sys.executable, str(ROOT / "deploy.py"), "demo", "--create-machine"],
                                cwd=self.root, env=environment, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Missing API key", result.stderr)


class CloudFixture:
    """Fake HTTP service; execute the actual deployed worker locally in a temp folder."""
    machine_id = "0199a1b2-c3d4-7000-8000-000000000001"

    def __init__(self, root, lose_database=False, execution_fails=False, never_sleeps=False):
        self.root = root
        self.phase = "running"
        self.remote_dir = None
        self.local_dir = root / "remote"
        self.executions = {}
        self.events = []
        self.lose_database = lose_database
        self.execution_fails = execution_fails
        self.never_sleeps = never_sleeps
        self.upload_count = 0

    def machine(self, retrieval=False):
        body = {"machine_id": self.machine_id, "vcpu": 1, "memory_mib": 2048,
                "storage_gib": 10, "autosleep_seconds": 300,
                "desired_state": "sleeping" if self.phase == "sleeping" else "running"}
        if retrieval:
            body["status"] = {"phase": self.phase, "reason": "test", "retryable": False,
                              "revision": "1", "memory_configured_mib": 2048,
                              "last_progress_at": "2026-10-02T00:00:00Z",
                              "last_transition_at": "2026-10-02T00:00:00Z"}
        else:
            body["phase"] = self.phase
        return body

    def execute(self, request):
        command = request["command"]
        self.events.append("exec:" + command[0])
        if self.phase != "running":
            raise AssertionError("An execution was issued before the machine was running")
        if command[0] == "/bin/sh":
            # Test environments already have Python; do not run system installation.
            return 0, "", ""
        if command[1] == "-c":
            self.upload_count += 1
            self.remote_dir = command[-1]
            command = [sys.executable, "-c", command[2], str(self.local_dir)]
        else:
            command = [sys.executable] + [arg.replace(self.remote_dir, str(self.local_dir))
                                          for arg in command[1:]]
        result = subprocess.run(command, input=request.get("stdin"), capture_output=True,
                                text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr

    def __call__(self, request):
        path = request.url.path
        base = f"/v1/machines/{self.machine_id}"
        if request.method == "POST" and path == "/v1/machines":
            self.events.append("create")
            body = json.loads(request.content)
            assert body == {"vcpu": 1, "memory_mib": 2048, "storage_gib": 10, "autosleep": "5m"}
            assert request.headers.get("idempotency-key")
            return httpx.Response(200, json=self.machine())
        if request.method == "GET" and path == base:
            self.events.append("phase:" + self.phase)
            return httpx.Response(200, json=self.machine(retrieval=True))
        if request.method == "POST" and path in {base + "/sleep", base + "/wake"}:
            action = path.rsplit("/", 1)[-1]
            self.events.append(action)
            self.phase = "sleeping" if action == "sleep" and not self.never_sleeps else "running"
            if action == "sleep" and self.lose_database:
                database = self.local_dir / "state" / "datasets.sqlite3"
                if database.exists():
                    database.unlink()
            return httpx.Response(200, json=self.machine())
        if request.method == "POST" and path == base + "/executions":
            body = json.loads(request.content)
            assert body["timeout_ms"] > 0
            if self.execution_fails:
                code, out, err = 1, "", "Intentional fixture failure"
            else:
                code, out, err = self.execute(body)
            eid = f"wexec-{len(self.executions)}"
            execution = {"execution_id": eid, "machine_id": self.machine_id,
                         "created_at": "2026-10-02T00:00:00Z", "log_capture": {},
                         "status": "succeeded" if code == 0 else "failed", "exit_code": code}
            self.executions[eid] = (execution, {"execution_id": eid, "stdout": out, "stderr": err,
                                               "stdout_truncated": False})
            return httpx.Response(200, json={**execution, "status": "queued"})
        if request.method == "GET" and path.startswith(base + "/executions/"):
            eid = path[len(base + "/executions/"):].split("/")[0]
            execution, output = self.executions[eid]
            if path.endswith("/output"):
                self.events.append("output:" + eid)
                return httpx.Response(200, json=output)
            self.events.append("retrieve:" + eid)
            return httpx.Response(200, json=execution)
        raise AssertionError(f"Unexpected SDK request: {request.method} {path}")


class SDKTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def run_fixture(self, fixture):
        with Dedalus(api_key="test-key-never-used-on-network", base_url="https://fixture.invalid",
                     max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(fixture))) as client:
            with contextlib.redirect_stdout(io.StringIO()):
                return deploy.cloud_demo(client, self.root / "report.json", poll_seconds=0)

    def test_sdk_deploy_sleep_wake_recovery_contract(self):
        fixture = CloudFixture(self.root)
        report = self.run_fixture(fixture)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["sleep_phase_observed"])
        self.assertEqual(report["before"], report["after"])
        self.assertEqual(report["query_after"], deploy.EXPECTED)
        self.assertEqual(fixture.upload_count, 1)
        self.assertEqual(fixture.phase, "sleeping")
        self.assertEqual(fixture.events.count("sleep"), 2)
        self.assertEqual(fixture.events.count("wake"), 1)
        self.assertLess(fixture.events.index("phase:sleeping"), fixture.events.index("wake"))
        for eid in fixture.executions:
            self.assertLess(fixture.events.index("retrieve:" + eid), fixture.events.index("output:" + eid))

    def test_missing_data_after_sleep_fails_and_still_sleeps_machine(self):
        fixture = CloudFixture(self.root, lose_database=True)
        with self.assertRaises(deploy.DemoError):
            self.run_fixture(fixture)
        report = json.loads((self.root / "report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["live_sleep_wake_verified"])
        self.assertEqual(fixture.phase, "sleeping")
        self.assertEqual(fixture.upload_count, 1)

    def test_execution_error_does_not_print_false_success(self):
        fixture = CloudFixture(self.root, execution_fails=True)
        with self.assertRaisesRegex(deploy.DemoError, "Intentional fixture failure"):
            self.run_fixture(fixture)
        report = json.loads((self.root / "report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["final_machine_phase"], "sleeping")
        self.assertNotIn("test-key-never-used-on-network", (self.root / "report.json").read_text())

    def test_sleep_acknowledgement_alone_is_not_proof(self):
        fixture = CloudFixture(self.root, never_sleeps=True)
        with Dedalus(api_key="test", base_url="https://fixture.invalid", max_retries=0,
                     http_client=httpx.Client(transport=httpx.MockTransport(fixture))) as client:
            api = deploy.Machines(client, timeout_seconds=0.01, poll_seconds=0)
            with self.assertRaisesRegex(deploy.DemoError, "Timed out"):
                api.sleep(fixture.machine_id)


if __name__ == "__main__":
    unittest.main()
