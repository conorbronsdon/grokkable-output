A config error left over from a deploy: tax-svc's v2.14.0 release (13:47 UTC) pointed at Avalara's sandbox endpoint instead of prod. The sandbox rate-limits at 10 req/s, prod traffic peaks around 45 req/s, so tax-svc started getting 429s, retried three times with 2s backoff, and that pushed latency past the orchestrator's 5s timeout — which checkout-svc turned into a 500. It was intermittent because traffic only crossed 10 req/s at peak; off-peak, no 429s, no problem.

I rolled back tax-svc to v2.13.2 at 15:12 UTC (pre-approved for sev2). 500 rate was back to baseline (0.02%) by 15:19 UTC and held stable over 30 minutes of monitoring.

The rollback drops the ZIP+4 enrichment feature that shipped in v2.14.0. Filed TAX-2211 to fix the endpoint config and re-deploy; also filed TAX-2212 proposing a config-diff review step for vendor endpoints in the deploy checklist, since that's the gap that let a sandbox URL reach prod.
