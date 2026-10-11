# Implementation status

The original ZIP is preserved in full. Its useful components provide starting
points for further development; status labels below describe current behavior.

| Item | Implemented | Remaining |
| --- | --- | --- |
| Research scaffold | JSON note and progress-state storage | Actual search calls, PDF processing, verified source extraction, restart cursor |
| Browser scaffold | JSON session and task-state storage | Playwright/browser wiring, real cookies, storage state loading, task scheduling |
| Code scaffold | Python subprocess execution, persistent venv, package install and history | Time/output limits, reliable exit reporting, an explicit isolation policy; a directory alone is not a security sandbox |
| Data scaffold | JSON metadata and sample result flow | Real import/query/chart logic in the original scaffold; the new focused example supplies real CSV/SQLite functionality |
| Slack scaffold | Local CLI conversation history and saved task entries | Slack event listener, credential configuration, scheduled delivery and real reasoning |
| MCP configuration files | Connection proposals for five template folders | Validation of current server packages, dependency installation and actual agent invocation |
| Original deploy scripts | Draft provisioning and deployment sequence | Correct SDK, execution polling, upload paths, task arguments and error/cleanup handling |
| Original CI | Syntax/configuration intent | A passing suite that verifies capabilities and does not suppress failures |
| New data example | Real CSV import, read-only SQL, persisted state, fresh-process recovery, 13 passing automated tests | Live deployment, confirmed sleep/wake, and saved-data recovery on an account with Machines access |

The new cloud runner uses `dedalus-sdk==0.6.0`, separate execution creation,
retrieval and output calls, and `status.phase` for machine state. It is verified
against the installed SDK and a fake HTTP service. That test is distinct from a
live deployment.

Original scripts remain under `design-original/` to preserve the design history.
Run the implemented example under `examples/persistent-data-agent/`.

No provider performance, activation-time or conversion claims have been
established by this repository. The original README's sample timings should not
be used as measured results.
