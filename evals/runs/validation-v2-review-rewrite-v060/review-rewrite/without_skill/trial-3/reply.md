Review

The draft has three problems. First, it overclaims certainty: "definitely the root cause" and the closing "the root cause was the cache key" state as settled what the source notes call unproven. The evidence is a cache key missing the tenant ID, observed in 7 of 312 failed requests — suggestive, not conclusive, since 305 failures were never traced. Second, "Production is fixed and ready" overstates the resolution. What actually happened is narrower: the failing path was disabled and error rate returned to baseline, but the fix hasn't been validated by the full integration suite, and the underlying cache bug is still in v4.8. Third, the draft's "Investigation update" narrative ("First I pulled... After checking a few possibilities I found...") plus the three labeled phases add process theater that isn't load-bearing for the decision — it doesn't change what the reader needs to do next. The recommendation itself (backport tomorrow, after the suite passes) is supported and worth keeping, along with the rollback rationale and the test status.

Rewrite

**Incident update**

Checkout errors stopped after the recommendations feature flag was disabled at 16:42 UTC; error rate returned to baseline by 16:47 UTC.

**Root cause (unconfirmed)**

The leading hypothesis is a recommendations cache key that omits the tenant ID, which could let one customer's session read another's cached recommendation and fail at checkout. This is supported by 7 of 312 failed requests we were able to trace — all 7 show the shared-entry pattern. The other 305 failures haven't been traced, so other mechanisms aren't ruled out yet.

**Current state**

Disabling the flag removed the failing path but isn't a fix. We didn't roll back to a pre-v4.8 build because v4.8 also ships a security patch we don't want to lose. All 418 existing unit tests and 6 new targeted regression tests pass; the full integration suite hasn't run yet.

**Decision needed**

Backport the cache-key fix to v4.8, or hold it for v4.9. Recommendation: backport tomorrow, once the full integration suite passes — the current test coverage doesn't yet include integration-level confirmation.

Cut as selection

- The three-phase "log review → trace inspection → mitigation" investigation narrative — narrative color, not needed to act on the update.
- "Production is fixed and ready" and the ✅ — replaced with the more accurate "disabling the flag removed the failing path, not a fix," since the root cause remains unproven and the fix is unvalidated.
- "Definitely the root cause" and the closing "the root cause was the cache key" — downgraded to "leading hypothesis," since only 7 of 312 failures were traced.
- The one-line "In summary, the incident is resolved" close — cut as a restatement that overstates resolution; the decision-needed section already carries the actionable content.
