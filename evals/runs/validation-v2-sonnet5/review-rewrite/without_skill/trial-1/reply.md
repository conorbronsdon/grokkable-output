Review

The draft has real structural and factual problems.

- **Overclaims presented as certainty.** "The recommendations cache key is definitely the root cause" and the closing "the root cause was the cache key" both overstate what the evidence supports. The source notes are explicit that root cause is not proven — the cache-key theory rests on 7 of 312 failed requests being traced, which is a small, non-representative sample. "Definitely" and unqualified declarative statements should not survive into a written update.
- **"Production is fixed and ready" is not supported.** What actually happened is that a symptom was suppressed (the feature flag was disabled) and error rate returned to baseline. That's not the same as "fixed" — the underlying cache-key defect, if it is the cause, is still in the code. The ✅ checkmark reinforces a false sense of closure.
- **Missing caveat.** The draft never states that other failure mechanisms haven't been ruled out. This is a load-bearing caveat given how thin the trace sample is, and its absence makes the root-cause claim look sturdier than it is.
- **Irrelevant narrative filler.** "First I pulled the error logs and then looked at traces. After checking a few possibilities..." and the Phase 1/2/3 labels describe process, not findings, and add no decision-relevant information.
- **The "In summary" line compounds the overclaim** by restating "resolved" and "root cause was" as settled facts, which is the same error twice.
- **What's actually solid and should stay:** the timeline (16:42/16:47 UTC), the rollback-vs-security-patch tradeoff and reasoning, the test status (418 unit + 6 regression pass, integration suite not yet run), the two-option decision framing, and the recommendation to backport tomorrow after the integration suite passes.

Rewrite

**Investigation update**

Checkout errors returned to baseline within 5 minutes of disabling the recommendations feature flag (16:42–16:47 UTC). Root cause is not yet confirmed.

**Root cause (unconfirmed)**

The leading hypothesis is a cache key that omits the tenant ID, which could let one customer's recommendation be served from another customer's cache entry, causing checkout to fail. This is based on 7 of 312 failed requests that were traced — a small sample, and other failure mechanisms haven't been ruled out.

**Current state**

Disabling the recommendations flag removed the failing path and restored baseline error rates, but this is a mitigation, not a fix — the underlying cause is still unconfirmed and, if it's the cache key, still present in the code. We didn't roll back release v4.8 because it also contains a security patch we want to keep.

Test status: all 418 unit tests and 6 new targeted regression tests pass. The full integration suite has not run yet.

**Next steps**

Decision needed: backport the cache-key fix to v4.8, or wait for v4.9. Recommendation: backport tomorrow, after the full integration suite passes and confirms the fix.

Cut as selection

I cut the "definitely," the ✅ "Production is fixed and ready" framing, the "root cause was the cache key" summary line, and the Phase 1/2/3 investigation narrative. None of these are supported by the underlying evidence (root cause is unconfirmed, only mitigated) or add decision-relevant content (the phase labels are process narration, not findings). I added back the "other failure mechanisms have not been ruled out" caveat, which was present in the source notes but missing from the draft, and reframed "fixed" as "mitigated" to match what the evidence actually shows.
