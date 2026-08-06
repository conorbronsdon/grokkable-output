**Short version: tax-svc v2.14.0 shipped with the Avalara *sandbox* host in config. I rolled tax-svc back to v2.13.2 at 15:12 UTC and the 500s are gone — error rate back to 0.02% baseline by 15:19, stable over 30 minutes of monitoring since.**

**The causal chain**

`tax-svc v2.14.0` (deployed 13:47 UTC) added a ZIP+4 enrichment call, and its config still pointed at `AVATAX_HOST=sandbox-rest.avatax.com`. The sandbox endpoint rate limits at 10 req/s; peak checkout traffic is ~45 req/s. So:

sandbox host → Avalara 429s → each 429 retried 3x with 2s backoff (up to +6s latency) → tax-svc p99 goes 210ms → 8.4s → blows past payment-orchestrator's 5s downstream timeout (`config/timeouts.yaml:22`) → `TaxLookupTimeout` → checkout-svc catches it as a generic `Exception` and rethrows as a 500.

That's why it was *intermittent*: off-peak traffic dips under 10 req/s, no 429s, no latency, no errors. 137 500s between 14:02-14:40 UTC, all on `POST /v2/checkout/complete`. Traced through req id `8f3a91` and confirmed the 429s directly in tax-svc logs.

**Why rollback and not something else**

Three options were on the table:
- **Rollback to v2.13.2** — fast, only cost is losing the ZIP+4 feature until we re-ship. Rollbacks are pre-approved for sev2 per runbook, so I took this one without waiting on you.
- **Hotfix config to the prod Avalara host** — correct fix, but needs a prod API key from the secrets team, ~1h. Too slow while we're actively dropping checkouts.
- **Raise the orchestrator timeout** — I'd argue against this even later. It masks the real problem and makes checkout slower for everyone.

**Follow-ups filed**

- **TAX-2211** — do the config fix properly (prod Avalara host + key) and re-ship ZIP+4.
- **TAX-2212** — the deploy checklist has no config-diff review step for vendor endpoints, which is the actual gap that let a sandbox host reach prod. Proposed adding one.

**Two things worth your judgment**

1. **The exception handling in checkout-svc is hiding signal.** It swallows `TaxLookupTimeout` into a generic 500 — a downstream timeout is arguably a 503, and either way it cost us time in diagnosis. Not in scope for what you asked, so I left it alone.
2. **I didn't audit other services for the same class of bug.** If sandbox-vs-prod endpoints are configured this way elsewhere, this recurs. Happy to sweep if you want it.
