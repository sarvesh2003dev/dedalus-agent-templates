# Dedalus persistence template: real CSV analysis

Built by Sarvesh as an independent onboarding prototype for Dedalus Machines.
This is the focused implementation of the data-analysis idea in the original
five-template pack.

The worker imports an actual CSV into SQLite, computes revenue by region, and
reloads the saved database in a new process. The cloud command deploys that same
worker, waits for a confirmed sleep, wakes the machine, and checks the data again.

**Verification status:** local process recovery and automated SDK contract tests
pass. A live Dedalus sleep/wake run is still pending Machines access. The contract
tests use a fake HTTP service and are not evidence of cloud persistence.

## What is implemented

- Real CSV parsing, typed SQLite columns, transactional writes and read-only SQL.
- A random proof token saved alongside the data before sleeping.
- Comparison of the database hash, data hash, source hash, row count and query
  results after waking. The worker and CSV are uploaded only once per run.
- The official `dedalus-sdk==0.6.0`, execution polling, error checks and timeouts.
- A JSON run report containing the machine ID and verification evidence.
- A final sleep request on both success and failure, with its result recorded.

This is a deterministic data worker. It does not claim autonomous LLM reasoning,
MCP integration, or production readiness. The other four templates are outside
this focused package.

## Try the working local example

Python 3.10 or later is required. This command has no third-party dependencies
and does not need an account:

```powershell
python deploy.py local-demo
```

On macOS/Linux, use `python3` in place of `python` if needed.

Each stage runs in a fresh Python process. The data genuinely comes from
`data-agent/sample-sales.csv`, which contains six sample sales totaling 790,000
cents. The result is APAC: 210,000, EU: 260,000, US: 320,000 cents. All amounts are
integers so the example does not introduce floating-point rounding in currency.

The report says `mode: local_process_restart` and
`live_sleep_wake_verified: false`. It proves local disk recovery, not a VM cycle.

## Get Machines access

1. Open [Dedalus Labs](https://www.dedaluslabs.ai/). As of October 2, 2026,
   the public site offers **Join waitlist**. Request Machines access if your
   account does not already have it.
2. Once access is enabled, use the Dashboard link in the
   [official quickstart](https://docs.dedaluslabs.ai/dcs/dm/quickstart) to create
   an API key for your organization.
3. Use the hidden terminal prompt below. The template does not save the key or
   upload it to the machine. Do not put it in a README, commit, screenshot or chat.

The [pricing page](https://docs.dedaluslabs.ai/dcs/dm/pricing) currently lists a
$0/month Hobby plan with a one-time signup credit. Compute is metered while awake;
storage continues to count toward the account's allowance while sleeping. Confirm
your account's available credits and storage before creating a machine.

## Install the deployment SDK

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe deploy.py check-access --prompt-key
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python deploy.py check-access --prompt-key
```

The access check only lists at most one machine; it does not provision anything.
An HTTP 401 usually indicates an authentication issue. An HTTP 403 requires
checking account permissions or Machines access with Dedalus.

## Run the actual deployment, sleep and recovery test

This command creates **one machine with 1 vCPU, 2 GiB RAM and 10 GiB disk** and
uses account credits. It leaves the machine sleeping, with the saved data intact.

```powershell
.\.venv\Scripts\python.exe deploy.py demo --create-machine --prompt-key
```

On macOS/Linux:

```bash
.venv/bin/python deploy.py demo --create-machine --prompt-key
```

Alternatively, set `DEDALUS_API_KEY` in your local environment and omit
`--prompt-key`. A dedicated existing test machine can be selected with
`--machine-id YOUR_MACHINE_ID` in place of `--create-machine`. That option will
sleep the selected machine, so use a machine reserved for this demo.

The command performs these steps:

1. Records the machine ID locally and waits until it is running.
2. Ensures Python is available and uploads only the worker and sample CSV into a
   unique `/home/machine/dedalus-data-demo/<run-id>/` directory.
3. Imports the CSV once, saves the random proof token, and verifies real SQL totals.
4. Requests sleep and waits until the API reports `status.phase == sleeping`.
5. Wakes the machine, waits for `running`, then starts a fresh worker process.
6. Queries the existing database and compares the saved token, hashes and totals.
7. Returns the machine to sleep and saves the final report under `runs/`.

`status: passed` and `live_sleep_wake_verified: true` in a report produced by
this live command indicate that the test completed. A failed command exits with
a nonzero status. A report from a test fixture is not a live service result.

The reported wake timings include client/API round trips and polling. They are
not a measurement of Dedalus's internal wake latency or a claim of a 50 ms result.

## Recovery semantics

The [current lifecycle documentation](https://docs.dedaluslabs.ai/dcs/dm/lifecycle)
states that files survive sleep and wake, while memory and running processes
reset. This worker deliberately restarts and reads SQLite from disk. It does
not rely on preserving RAM or keeping a process alive.

If a network error interrupts a run, inspect its JSON report for `machine_id`
and `final_machine_phase`. A value of `unconfirmed` means you should check the
dashboard and sleep the machine manually. Autosleep is configured to five
minutes as an additional fallback. If provisioning times out before an ID is
returned, check the dashboard for a created machine before retrying.

Machines are never automatically deleted. Delete a demo machine in your dashboard
when you no longer need its saved data; deletion loses that data.

## Use your own CSV locally

```powershell
python data-agent/agent.py --state-dir runs/my-data load --csv sales.csv --name sales --proof-token my-first-import
python data-agent/agent.py --state-dir runs/my-data query --sql "SELECT * FROM sales LIMIT 10"
python data-agent/agent.py --state-dir runs/my-data snapshot --name sales
```

Use simple column names containing letters, digits and underscores. This starter
limits imports to 10 MB, 100 columns and 100,000 rows, and query output to 1,000
rows. Existing datasets are not replaced. The cloud verification command uses
the bundled sample with known expected totals; it is not a general CSV uploader.

## Run the tests

After installing the SDK:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover fresh-process persistence, malformed and missing inputs, read-only
queries, data corruption, the SDK's request/response structure, confirmed sleep,
failed executions, missing state after wake, and cleanup. They never contact the
Dedalus API. GitHub Actions runs these checks without account secrets.

## Files

```text
deploy.py                 Local demo, access check and cloud lifecycle runner
data-agent/agent.py        Actual CSV/SQLite worker
data-agent/sample-sales.csv
requirements.txt          Official Machines SDK pin
tests/test_template.py    Local and fake-HTTP SDK tests
.github/workflows/test.yml
```

Official references:
[Quickstart](https://docs.dedaluslabs.ai/dcs/dm/quickstart),
[Executions](https://docs.dedaluslabs.ai/dcs/dm/executions),
[Lifecycle](https://docs.dedaluslabs.ai/dcs/dm/lifecycle).

MIT licensed; original project copyright retained.
