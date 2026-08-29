Root cause: a leftover sandbox config. Tax-svc's 13:47 UTC deploy (v2.14.0) added a ZIP+4 tax enrichment call, but its config pointed at Avalara's sandbox endpoint instead of prod. The sandbox rate-limits at 10 req/s; our peak traffic is ~45 req/s, so it started returning 429s. Each 429 triggered a retry with 2s backoff (up to 3x), pushing tax-svc latency past the orchestrator's 5s timeout. That timeout becomes a `TaxLookupTimeout`, which checkout-svc's generic exception handler turns into a 500. It only showed up intermittently because traffic drops below 10 req/s off-peak, so no rate limiting then.

I rolled back tax-svc to v2.13.2 at 15:12 UTC (pre-approved for sev2). 500 rate is back to baseline (0.02%) as of 15:19 UTC, stable through 30 minutes of monitoring.

Rollback drops ZIP+4 enrichment for now. Filed TAX-2211 to point the config at the correct Avalara prod host and re-deploy — that needs a prod API key from the secrets team, roughly an hour of lead time once someone picks it up. Also filed TAX-2212: our deploy checklist has no config-diff review step for vendor endpoints, which is how a sandbox host reached prod. Worth adding before this bites again on a different service.

Want me to pick up TAX-2211 now, or hand it to whoever owns tax-svc?
