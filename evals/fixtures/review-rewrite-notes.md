# Feature-flag incident: source notes and draft

## Verified state

- Checkout recovered after the recommendations feature flag was disabled at
  16:42 UTC. Error rate returned to baseline by 16:47 UTC.
- The root cause is not proven. The strongest evidence is a cache key that
  omits the tenant ID: seven sampled traces show two customers receiving the
  same cached recommendation entry.
- Only 7 of 312 failed requests were traced. Other failure mechanisms have not
  been ruled out.
- A rollback was considered but not performed because release v4.8 also
  contains a security patch. Disabling the feature flag removed the failing
  path without removing that patch.
- All 418 unit tests pass. Six new targeted regression tests pass. The full
  integration suite has not run yet.
- Decision needed: backport the cache-key fix to v4.8 or wait for v4.9.
- Recommendation: backport tomorrow, after the full integration suite passes.

## Draft to review and rewrite

**Investigation update**

First I pulled the error logs and then looked at traces. After checking a few
possibilities I found the cache issue. Phase 1 was log review, Phase 2 was trace
inspection, and Phase 3 was mitigation.

**Root cause**

The recommendations cache key is definitely the root cause. It leaves out the
tenant ID, so customer A -> shared cache entry -> customer B gets the wrong
recommendation -> checkout fails. I saw this in seven traces out of 312 failed
requests.

**Resolution**

✅ Production is fixed and ready. I disabled the recommendations flag at 16:42
UTC and errors were back to baseline by 16:47. I did not roll back because v4.8
also has a security patch. The 418 unit tests and six regression tests pass, but
I have not run the full integration suite.

**Next steps**

We can either backport the cache-key change to v4.8 or wait for v4.9. I think we
should backport tomorrow after the integration suite passes.

In summary, the incident is resolved, the root cause was the cache key, and the
next step is a backport.
