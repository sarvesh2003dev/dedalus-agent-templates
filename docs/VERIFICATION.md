# Verification record

Checked locally on October 11, 2026 with Python 3.13 and `dedalus-sdk==0.6.0`.

- All 13 implemented-example tests passed.
- The original-file preservation test passed: all 27 original files match the
  uploaded ZIP byte for byte, and the exact source archive is retained.
- A real local CSV/SQLite run recovered the same proof token, database hash,
  row hash and query results in fresh processes.
- Sample totals matched: APAC 210,000 cents, EU 260,000 cents and US 320,000 cents.
- A scan of source text found no real API-key or GitHub-token patterns.

The automated cloud workflow test uses a fake HTTP service with the official
SDK and runs the actual uploaded worker in a temporary local directory. It
checks execution completion, confirmed phase transitions, missing data, and
cleanup. It is not a live cloud result.

Live Dedalus deployment and sleep/wake verification remain pending Machines
access. There is no measured provider wake-latency or conversion result.

Original source archive SHA-256:

```text
52c23c9e8fe2486b04c3f2ae9dec8bffaecee2395e8813e3b27f1dcbecfe164d
```
