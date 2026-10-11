# Contributing

Use `docs/` for design changes and `examples/` for implemented, runnable examples.
Keep `design-original/` and the original source ZIP intact; automated checks
verify their hashes against `preservation-manifest.json`.

For an implemented template, include a README describing its actual behavior,
required accounts, durable state, restart procedure, and meaningful tests. Label
simulated results clearly. Do not describe proposed integrations as completed.

For cloud demonstrations, include lifecycle verification, execution error
handling, timeouts, and a plan for returning machines to sleep. Never commit
API keys, saved authenticated browser cookies or personal conversation exports.

Run both test commands listed in the root README before publishing changes.
