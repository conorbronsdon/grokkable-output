# Raw investigation log (agent's working notes)

Task from user: "checkout flow is intermittently 500ing in prod, find out why"

- checked api-gateway logs 14:02-14:40 UTC: 137 500s, all POST /v2/checkout/complete
- traced req id 8f3a91 → checkout-svc → payment-orchestrator → tax-svc
- tax-svc p99 latency 14:00-14:30: 8.4s (baseline 210ms)
- payment-orchestrator has 5s downstream timeout (config/timeouts.yaml line 22), so tax-svc calls time out → orchestrator raises TaxLookupTimeout → checkout-svc catches generic Exception and rethrows as 500
- why is tax-svc slow? deploy history: tax-svc v2.14.0 deployed 13:47 UTC today
- v2.14.0 diff: added ZIP+4 enrichment call to vendor API (Avalara sandbox endpoint left in config! `AVATAX_HOST=sandbox-rest.avatax.com`)
- sandbox endpoint rate limits at 10 req/s, prod traffic is ~45 req/s at peak
- confirmed: 429 responses from Avalara in tax-svc logs, each 429 triggers retry with 2s backoff x3 = up to 6s added latency
- so: sandbox host config error → rate limiting → retries → latency > 5s timeout → 500s
- only intermittent because traffic dips below 10 req/s off-peak, no 429s then
- fix options: (a) rollback tax-svc to v2.13.2 (fast, loses ZIP+4 feature), (b) hotfix config to prod Avalara host (needs prod API key from secrets team, ~1h), (c) raise orchestrator timeout (bad — masks problem, hurts checkout UX)
- rolled back to v2.13.2 at 15:12 UTC per runbook (rollbacks pre-approved for sev2)
- 500 rate back to baseline (0.02%) by 15:19 UTC, monitored 30 min, stable
- filed JIRA TAX-2211 for the config fix; deploy checklist gap: no config-diff review step for vendor endpoints — proposed adding to checklist in TAX-2212
