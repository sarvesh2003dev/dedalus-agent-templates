# Development roadmap

## 1. Validate the implemented data example in the cloud

- Enable Machines access and check API authentication.
- Run the bundled deployment → load → sleep → wake → verify sequence.
- Retain the JSON result with confirmed lifecycle states, matching data hashes
  and query totals.
- Record client-observed recovery time without presenting it as internal VM
  latency.

Acceptance: a real cloud run recovers the existing database without re-uploading
or regenerating its data, and the machine's final sleeping state is confirmed.

## 2. Implement real browser session recovery

- Use a real browser context and persist its supported storage state.
- Use a controlled test application with a test login.
- Restart the browser after wake and verify the logged-in session and a real
  task result.

Acceptance: the recovered browser accesses the protected test page with the
saved session, without fake cookie values or invented scrape results.

## 3. Implement research retrieval

- Connect a real search service and record actual source URLs.
- Fetch and parse one supported document type.
- Persist notes and a progress cursor; resume work without repeating completed
  steps.

Acceptance: a completed brief can be traced to retrieved sources, and a restarted
worker loads the saved notes.

## 4. Strengthen code execution

- Define the trust boundary and supported languages.
- Enforce execution timeout and output limits.
- Report nonzero exits correctly and verify that installed dependencies survive.

Acceptance: a repeated run reuses its persistent environment, and timeout/error
cases produce clear failures.

## 5. Connect Slack and reminders

- Add a configured Slack event listener with signature verification.
- Store conversation state with a clear retention policy.
- Use an external scheduler for wake and reminder delivery when the VM sleeps.

Acceptance: real events receive responses, reminders are delivered at their
scheduled time, and saved context is recovered after restart.

## 6. Test the onboarding hypothesis

Ask developers unfamiliar with the project to choose a template and complete the
recovery flow. Measure completion and time to first verified result. Use those
observations to decide whether a dashboard template chooser is worth building.
