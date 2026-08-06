Found it and mitigated it: tax-svc v2.14.0 shipped with `AVATAX_HOST` still pointing at Avalara's sandbox endpoint, and the sandbox rate-limits at 10 req/s. I rolled tax-svc back to v2.13.2 at 15:12 UTC and the 500 rate is back to baseline.

The chain: v2.14.0 deployed at 13:47 UTC and added a ZIP+4 enrichment call to the Avalara vendor API. At peak we push ~45 req/s, well over the sandbox limit, so Avalara returned 429s (confirmed in tax-svc logs). Each 429 triggers a retry with 2s backoff, up to three times, adding as much as 6s of latency — tax-svc p99 went from 210ms to 8.4s. The payment-orchestrator's downstream timeout is 5s (`config/timeouts.yaml` line 22), so those calls timed out and raised TaxLookupTimeout, which checkout-svc catches as a generic Exception and rethrows as a 500. That produced 137 500s on POST /v2/checkout/complete between 14:02 and 14:40 UTC. It was intermittent only because off-peak traffic drops below 10 req/s and stops tripping the rate limit.

Evidence for the fix working: 500 rate at 0.02% by 15:19 UTC, stable across 30 minutes of monitoring. Rollback was pre-approved for sev2 under the runbook, so I didn't wait on an approval.

One decision for you: the rollback also removes the ZIP+4 enrichment feature. The real fix (TAX-2211) is pointing `AVATAX_HOST` at the production Avalara host, which needs a prod API key from the secrets team — roughly an hour of their time. Do you want me to open that request, or does someone on your side own the secrets ask?

Two things worth flagging that you didn't ask about. The deploy checklist has no config-diff review step for vendor endpoints, which is why a sandbox host reached prod unnoticed; I proposed adding one in TAX-2212. And checkout-svc turning a known TaxLookupTimeout into an opaque 500 is its own bug — it cost time here, though I didn't dig into that handler.

Scope limit: I only looked at tax-svc. I did not check whether other services carry the same sandbox endpoint in their configs.
