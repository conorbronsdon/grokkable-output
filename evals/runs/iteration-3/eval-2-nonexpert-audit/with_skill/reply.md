Less bad than the headline number, but two items are worth fixing this week. The scan flagged 23 issues. Three of them actually matter for your app; the other 20 are either in tools that only run on developer machines and never ship to customers, or in code a stranger can't reach.

Here are the three, in the order I'd fix them.

**1. The login-token library (jsonwebtoken) — fix today.** This is the code that checks whether a session token is genuine, so it sits directly in the path of every logged-in request. It has a known flaw in how it decides which signing method to trust. Exploiting it would require an attacker to control key material we don't hand out, so I don't think it's currently reachable — but it's the authentication layer, and I'd rather not reason my way into leaving it. The upgrade changes behavior slightly, so three places in the code need a small edit alongside it. Roughly 1–2 hours including tests.

**2. The avatar-import feature (axios) — fix this week.** When a user imports an avatar, they give us a web address and our server fetches it. The library doing that fetch has a flaw that lets a crafted address point the fetch somewhere it shouldn't go, including internal systems not meant to be reachable from the internet. This is the most realistically attackable of the three, because the user already controls the input. The fix is the upgrade plus a list of addresses we're willing to fetch from. Roughly 2–3 hours.

**3. lodash — whenever.** It's a real flaw, but the only place we use that library is a build script that generates the sitemap. It never runs during a customer request. Five-minute upgrade, no breaking changes. Hygiene, not risk.

Everything else — 11 moderate and 5 low, plus 4 of the 5 "high" ones — is either developer tooling or indirect dependencies outside the request path. Those belong in a normal maintenance update, not an emergency.

Two things you should know beyond the list. I searched 30 days of error logs for signs anyone has attempted either the lodash or avatar-import attack and found nothing; that's reassuring, not proof, since it would only catch attempts that produced errors. And there's a process gap: the repo has no automated dependency updates configured (Dependabot or Renovate), so nothing tells us about this except a manual scan. Setting that up is under an hour and prevents the next version of this conversation.

One decision for you: do you want me to start on the login-token fix today, or batch all three into one block of work later this week?
