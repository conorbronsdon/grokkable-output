Short version: it's not as bad as "23 vulnerabilities" sounds, but there are two real ones we should fix fast, and one process gap worth closing.

**What the scan found:** npm flagged 23 issues (2 critical, 5 high, 11 moderate, 5 low). That number looks scary, but most of it is noise — 17 of the 23 are in dev/build tooling that never ships to production, or in transitive packages that don't run in any code path an attacker can reach.

**What actually matters — 3 things:**

1. **Auth library (jsonwebtoken)** — this is the one that verifies session tokens on every login. It's flagged critical, and even though exploiting it would require conditions we don't currently expose, it's sitting in our auth layer, so I want to treat it as real rather than bet on that. Fix takes 1-2 hours including tests. **Doing this today.**

2. **HTTP library (axios) — SSRF risk** — this one's in the code that fetches a user-submitted URL for avatar imports. That's a legitimate exploitable shape: someone could hand us a malicious URL. Fix is a version bump plus adding a URL allowlist, about 2-3 hours. **Doing this this week.**

3. **lodash (build script only)** — flagged critical, but it's only used in a script that generates our sitemap, not in anything a user request touches. Real-world risk is low. Trivial fix (5 minutes, no breaking changes), rolling it in with #1.

Everything else — the other 11 moderate and 5 low items, plus 4 of the 5 "high" ones — are dev tooling or transitive dependencies with no path to production. Normal maintenance, not urgent.

**Have we been hit?** I checked 30 days of error logs for signatures of these specific issues — nothing. No evidence of exploitation.

**One gap to close after this:** we don't have automated dependency update alerts (no Dependabot/Renovate) set up, which is how this pile accumulated unnoticed. I'd like to turn that on once the two urgent fixes land so we get a steady trickle of small updates instead of a scary pile every few months.

Net: real risk existed, mostly at the auth layer, nothing indicates it's been exploited, and it's a few hours of work to close the actual gaps — not a fire drill, but worth doing this week, not "eventually."
