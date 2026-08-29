Found it — checkout was 500ing because of a config mistake, not a code bug.

**Root cause:** tax-svc v2.14.0 (deployed 13:47 UTC) added a ZIP+4 enrichment call, but shipped with the Avalara *sandbox* endpoint still in config (`AVATAX_HOST=sandbox-rest.avatax.com`). Sandbox rate-limits at 10 req/s; we run ~45 req/s at peak. That triggered 429s → retries (2s backoff x3, up to 6s) → tax-svc latency spiked to 8.4s p99 (baseline 210ms) → blew through the orchestrator's 5s downstream timeout → `TaxLookupTimeout` → checkout-svc catches it as a generic Exception and rethrows as a 500. Intermittent because it only bites when traffic is above ~10 req/s, so it cleared off-peak.

**Chain:** api-gateway (137x 500s on POST /v2/checkout/complete, 14:02–14:40) → checkout-svc → payment-orchestrator (5s timeout, config/timeouts.yaml:22) → tax-svc → sandbox Avalara host.

**Action taken:** Rolled back tax-svc to v2.13.2 at 15:12 UTC (pre-approved sev2 rollback path). 500 rate back to baseline (0.02%) by 15:19, held stable for 30 min of monitoring.

**Follow-up filed:**
- TAX-2211 — swap in the prod Avalara host/key to get ZIP+4 back safely (needs a prod API key from secrets team, ~1h turnaround)
- TAX-2212 — add a config-diff review step for vendor endpoints to the deploy checklist, since that's the actual gap that let this ship

Rejected raising the orchestrator timeout as a fix — would've masked the problem and made checkout feel slower for everyone instead of fixing the rate-limiting.
