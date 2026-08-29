Found it — root cause, fix, and status:

**Root cause:** tax-svc v2.14.0 (deployed 13:47 UTC) shipped with its new ZIP+4 enrichment call pointed at the Avalara *sandbox* endpoint instead of prod (`AVATAX_HOST=sandbox-rest.avatax.com` left in config). Sandbox rate-limits at 10 req/s; we run ~45 req/s at peak, so tax-svc started getting 429s, retried 3x with 2s backoff (up to +6s latency), blew past payment-orchestrator's 5s downstream timeout, orchestrator threw `TaxLookupTimeout`, and checkout-svc caught that as a generic Exception → 500. That's also why it was intermittent — traffic dips below 10 req/s off-peak, so no 429s and no timeouts then.

**Chain confirmed via trace:** api-gateway (137 500s, all `POST /v2/checkout/complete`, 14:02–14:40) → checkout-svc → payment-orchestrator → tax-svc, with tax-svc p99 spiking to 8.4s (baseline 210ms), and 429s from Avalara visible in tax-svc logs.

**Action taken:** Rolled back tax-svc to v2.13.2 at 15:12 UTC (pre-approved sev2 rollback path). 500 rate back to baseline (0.02%) by 15:19 UTC, monitored 30 min stable. We lose the ZIP+4 enrichment feature until the config's fixed.

**Follow-up filed:**
- TAX-2211 — hotfix the Avalara host to prod (needs a prod API key from the secrets team, ~1h) so ZIP+4 can go back out safely.
- TAX-2212 — add a config-diff review step for vendor endpoints to the deploy checklist; this would've caught the sandbox host before it shipped.

Didn't touch the orchestrator's 5s timeout — raising it would've masked the real problem and made checkout feel slower for users, so that's off the table as a "fix."
