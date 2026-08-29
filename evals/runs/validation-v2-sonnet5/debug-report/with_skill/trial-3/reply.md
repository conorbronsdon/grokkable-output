A misconfigured vendor endpoint in the tax service caused the checkout 500s, and it's already fixed.

Here's the chain: checkout calls payment-orchestrator, which calls tax-svc, which has a 5s timeout. Tax-svc deployed v2.14.0 at 13:47 UTC today, adding a ZIP+4 enrichment call to Avalara — but the config pointed at the sandbox endpoint (`AVATAX_HOST=sandbox-rest.avatax.com`), which rate-limits at 10 req/s. Prod peak traffic is ~45 req/s, so sandbox started returning 429s, each one triggering a retry with backoff (up to 6s), which blew past the 5s timeout and surfaced as a 500 in checkout-svc. It was intermittent because traffic only exceeded 10 req/s during peak; off-peak requests sailed through with no 429s.

I rolled back tax-svc to v2.13.2 at 15:12 UTC (pre-approved for sev2). 500 rate is back to baseline (0.02%) and stable through 30 minutes of monitoring as of 15:19 UTC.

Rollback loses the ZIP+4 feature for now. The real fix is pointing tax-svc at the production Avalara host, which needs a prod API key from the secrets team — filed as TAX-2211, about an hour of work. I also filed TAX-2212 to add a config-diff review step for vendor endpoints to the deploy checklist, since that's the gap that let a sandbox host ship to prod.

Want me to pick up TAX-2211 now, or are you handling the secrets-team handoff?
