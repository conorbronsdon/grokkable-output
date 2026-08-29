Found it. Checkout flow was 500ing on POST /v2/checkout/complete — 137 errors between 14:02–14:40 UTC.

**Root cause:** tax-svc v2.14.0 (deployed 13:47 UTC) shipped with a sandbox Avalara endpoint left in config (`AVATAX_HOST=sandbox-rest.avatax.com`) instead of prod, added as part of a new ZIP+4 enrichment call. Sandbox rate-limits at 10 req/s; we run ~45 req/s at peak. That triggered 429s → retries with 2s backoff x3 (up to 6s added latency) → blew past payment-orchestrator's 5s downstream timeout → TaxLookupTimeout → checkout-svc's generic exception handler turned it into a 500. Intermittent because it only bit when traffic was above the 10 req/s threshold — clean off-peak.

**Fix:** Rolled back tax-svc to v2.13.2 at 15:12 UTC (pre-approved sev2 rollback). 500 rate back to baseline (0.02%) by 15:19, held stable for 30 min of monitoring.

**Follow-up:**
- TAX-2211 — reintroduce ZIP+4 with the correct prod Avalara host/key
- TAX-2212 — add a config-diff review step for vendor endpoints to the deploy checklist (that's the gap that let this ship)

We lost the ZIP+4 enrichment feature for now, but checkout's healthy. Let me know if you want me to pick up either JIRA ticket.
