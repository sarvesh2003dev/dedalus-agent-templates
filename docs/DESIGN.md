# Onboarding design

## Product hypothesis

A new user can understand the value of a persistent agent runtime by doing a
small useful task, sleeping the machine, and recovering a recognizable artifact.
Templates provide specific starting points for that experience.

The hypothesis should be validated with actual users. The original ZIP's
activation-time and conversion numbers are illustrative, not measured results.

## Template chooser

Each template card should show the task, the artifact it saves, required external
accounts, implementation status, and approximate resources. A user should see
whether they are choosing a working example or exploring a proposed integration.

| User intent | Starting template | Durable artifact | Integration needed |
| --- | --- | --- | --- |
| Build a research brief | Research | Notes, sources and progress cursor | Search API, PDF parsing, optional LLM |
| Return to an authenticated workflow | Browser | Real browser storage state and task output | Browser engine and application login |
| Reuse a computation environment | Code | Virtual environment, source files and run history | Execution limits and isolation policy |
| Explore uploaded business data | Data | SQLite dataset and query results | Implemented locally in the included example |
| Remember a team's discussions | Slack | Conversation state and reminder queue | Slack app, event endpoint, delivery scheduler |

## First-use flow

1. Choose a template and inspect its sample task.
2. Check access and disclose the machine resources before provisioning.
3. Deploy and run the sample task.
4. Show the saved artifact and its location.
5. Sleep the machine and wait for a confirmed sleeping state.
6. Wake it, start a fresh worker, and recover the artifact.
7. Show what matched: a proof token, content digest or a meaningful task result.
8. Offer a next task that builds on the saved work.

The implemented data example exercises this flow locally and contains a prepared
cloud runner. It currently requires a live account test to validate steps 5–6
against Dedalus Machines.

## Recovery model

Workers serialize useful task state to the filesystem and reload it when they
start. The documented Machines lifecycle preserves files; applications should
restart their processes after wake. Filesystem persistence and resuming an
in-memory execution cursor are different guarantees. Each template should state
which saved state it can recover and what work needs to be repeated.

For the data example, SQLite transactions save the dataset and a unique token.
The verification compares the same file and query results after restart. It does
not recreate the dataset during recovery.

## Evidence to collect

- Successful completion of the sample task.
- Correct recovery of the saved artifact after a confirmed sleep/wake cycle.
- Client-observed time from the wake request to usable recovered data.
- Setup failures and the steps that caused them.
- User time to the first verified result, measured across real attempts.

Internal machine wake latency requires a different measurement from a client
script's API round trips and polling. Label these measurements explicitly.

## Proposed dashboard controls

Each deployed template could show Run sample, Inspect saved state, Sleep,
Wake and verify, and View logs. The result panel should explain what was checked
and display errors when recovery fails. A failure must not be presented as a
successful activation.

This document specifies a possible interface. It is not an implemented website
or dashboard.
