A leftover sandbox config in today's tax-svc deploy caused the 500s — it's fixed, checkout is back to normal.

Here's the chain: tax-svc v2.14.0 (deployed 13:47 UTC) added a ZIP+4 enrichment call, but its config still pointed at Avalara's sandbox endpoint instead of prod. The sandbox rate-limits at 10 req/s, prod traffic peaks around 45 req/s, so tax-svc started getting 429s and retrying (up to 6s of added latency). That blew past the orchestrator's 5s downstream timeout, which raised a TaxLookupTimeout that checkout-svc turned into a generic 500. It was intermittent because traffic only exceeded 10 req/s at peak — off-peak there were no 429s and no failures.

I rolled tax-svc back to v2.13.2 at 15:12 UTC (pre-approved for sev2). 500 rate returned to baseline (0.02%) by 15:19 UTC and stayed stable over 30 minutes of monitoring.

Two follow-ups filed: TAX-2211 to fix the Avalara host config and re-ship ZIP+4 enrichment (needs a prod API key from the secrets team, ~1h once someone picks it up), and TAX-2212 to add a config-diff review step for vendor endpoints to the deploy checklist, since that's the gap that let this ship.

Nothing needed from you right now — rollback's holding. Want me to pick up TAX-2211 or leave it for whoever owns the Avalara integration?
