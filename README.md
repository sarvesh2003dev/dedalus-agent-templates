# Dedalus Agent Templates

An independent onboarding design by Sarvesh: help developers choose an agent use
case, see useful work saved to disk, and recover that work after a machine wakes.

This repository keeps the full five-template concept and adds a concrete CSV and
SQLite example. It is a design proposal with an implemented persistence worker.
Live Dedalus sleep/wake verification is pending Machines access.

## The five ideas

| Template | Product idea | What the original scaffold implements today |
| --- | --- | --- |
| Research | Continue research from saved notes | Saves query history and simulated findings to JSON; search and PDF processing need integration |
| Browser | Reuse a saved browser session | Saves simulated cookies and scrape output; a real browser session needs integration |
| Code | Reuse installed dependencies and execution history | Runs Python in a persistent virtual environment; resource limits and a reviewed isolation policy remain to implement |
| Data | Upload a dataset once and return to the analysis later | Original scaffold simulates loading, SQL and charts; the new example imports real CSV data and runs real SQLite queries |
| Slack | Keep conversation context across sessions | Persists messages entered through the local CLI; Slack events, reminder delivery and LLM reasoning need integration |

All five original agents, requirements, MCP configuration files, READMEs,
deployment scripts, contribution notes, license and CI file are available in
[`design-original/`](design-original/). The exact uploaded ZIP is retained in
[`source-archives/`](source-archives/).

The original files are preserved as submitted. Some original documentation claims
production readiness or real integrations that the scaffolds do not implement.
Use this README and the [implementation status](docs/STATUS.md) as the current
description. Treat the original deploy scripts as historical prototype material.

## Try the implemented example

Requires Python 3.10 or later; the local demonstration needs no account or
third-party packages:

```bash
python examples/persistent-data-agent/deploy.py local-demo
```

The worker reads six actual sample sales, saves them in SQLite, exits, and reloads
the same database in fresh processes. It verifies the saved proof token, database
and data hashes, row count, and the revenue totals by region.

For installation and the prepared cloud test, see the
[example guide](examples/persistent-data-agent/README.md). The cloud runner uses
the official Machines SDK, waits for confirmed sleeping and running phases, and
leaves the machine sleeping after the test. An account with Machines access is
required; a local result does not establish cloud sleep/wake behavior.

## Explore the design

- [Onboarding design](docs/DESIGN.md): template chooser, activation flow, and what
  evidence a user should see.
- [Implementation status](docs/STATUS.md): capabilities and unfinished work for
  every template.
- [Development roadmap](docs/ROADMAP.md): steps toward working integrations.
- [Preservation manifest](preservation-manifest.json): SHA-256 hashes for the
  original archive and all 27 original files.

## Run the automated checks

```bash
python -m pip install -r examples/persistent-data-agent/requirements.txt
python -m unittest discover -s examples/persistent-data-agent/tests -v
python -m unittest discover -s tests -v
```

These tests check real local file recovery, the deployment SDK contract using a
fake HTTP service, error handling, and exact preservation of the original ZIP
items. They do not create cloud machines or use account secrets.

## Repository layout

```text
design-original/                    All five original scaffolds and docs
source-archives/                    Original ZIP, byte for byte
examples/persistent-data-agent/     Implemented CSV/SQLite worker and cloud runner
docs/                               Design, status and roadmap
tests/                              Original-file preservation checks
.github/workflows/                  Active tests for this repository
```

This project is an independent prototype, with no claim of Dedalus endorsement.
MIT licensed; original copyright retained.
