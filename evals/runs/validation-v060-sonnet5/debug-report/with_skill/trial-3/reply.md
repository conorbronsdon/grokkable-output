A config error in tax-svc, now rolled back and stable.

The v2.14.0 deploy at 13:47 UTC added ZIP+4 tax enrichment but left the vendor endpoint pointed at Avalara's sandbox host, which rate-limits at 10 req/s. Prod traffic peaks around 45 req/s, so tax-svc started getting 429s, each one triggering a retry with backoff that added up to 6 seconds of latency. The payment-orchestrator's downstream timeout is 5 seconds, so those slow calls timed out, checkout-svc caught the resulting exception and returned a 500. It only showed up intermittently because traffic dips below the 10 req/s threshold off-peak, where no rate limiting occurred.

I rolled back tax-svc to v2.13.2 at 15:12 UTC (pre-approved for sev2 per the runbook). 500 rate returned to baseline (0.02%) by 15:19 UTC and has held stable for 30 minutes of monitoring since.

Two follow-ups filed: TAX-2211 to fix the sandbox host config so ZIP+4 can redeploy safely, and TAX-2212 to add a config-diff review step for vendor endpoints to the deploy checklist, since that's the gap that let this ship.

Rollback lost the ZIP+4 enrichment feature — worth flagging if anything downstream depends on it before TAX-2211 lands.
