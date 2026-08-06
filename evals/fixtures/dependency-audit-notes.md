# Raw audit output (agent's working notes)

Task from user (a non-engineer founder): "someone told me our app has security problems with its dependencies, how bad is it, what should we do"

npm audit + manual review of package.json (App: customer-facing Next.js SaaS, handles payment info via Stripe, stores user PII in Postgres):

- 23 advisories total from npm audit: 2 critical, 5 high, 11 moderate, 5 low
- critical #1: lodash 4.17.15 → prototype pollution (CVE-2020-8203). BUT: only used server-side in a build script (scripts/gen-sitemap.js), not in request path. Real exposure: low. Fix: bump to 4.17.21, zero breaking changes, 5 min.
- critical #2: jsonwebtoken 8.5.1 → algorithm confusion (CVE-2022-23529 family). This one IS in the request path — it verifies session tokens in middleware/auth.ts. Practical exploitability requires attacker-controlled key material which we don't expose, but this is the auth layer; treat as real. Fix: bump to 9.0.2 — breaking change: verify() now rejects tokens without alg allowlist; need to pass {algorithms:['HS256']} in 3 call sites. Est 1-2h with tests.
- 5 high: 4 are in dev-only tooling (webpack-dev-server x2, nodemon, jest-environment-jsdom) — not shipped to prod, near-zero exposure. 1 real: axios 0.21.1 SSRF (CVE-2021-3749) used in server/webhooks.ts fetching user-supplied URLs for avatar import — actually exploitable shape (user controls the URL). Fix: bump axios + add URL allowlist. Est 2-3h.
- 11 moderate + 5 low: all transitive, none in request path, standard bumps
- no evidence of active exploitation in logs (checked 30 days of error logs for pollution/SSRF signatures, nothing)
- overall: 3 things actually matter (jsonwebtoken, axios SSRF, then lodash for hygiene). The scary "23 vulnerabilities!" number is mostly dev tooling noise.
- recommended order: jsonwebtoken today (auth layer), axios this week (real exploit shape), everything else in a normal maintenance bump
- one process gap: no automated dependency updates (no dependabot/renovate config in repo)
