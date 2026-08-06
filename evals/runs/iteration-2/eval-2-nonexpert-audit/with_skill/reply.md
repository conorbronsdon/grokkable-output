Less bad than the headline number, but two items need real work this week and one of them touches login. The scan flagged 23 problems. Twenty of them are either in tools that only run on our own machines while we build the app (they never ship to customers) or are deep in the dependency tree where our code can't reach them. Three are worth acting on. I also searched 30 days of error logs for signs that anyone has actually tried these attacks against us and found nothing.

Here are the three, in the order I'd do them:

1. The session-token library (jsonwebtoken), today. This is the code that checks whether a logged-in user's token is genuine. Our version has a known flaw in how it validates tokens. Actually exploiting it would require an attacker to control cryptographic material we don't hand out, so I don't believe we're exploitable right now — but this is the front door, and I don't want to be clever about the front door. The fix is an upgrade plus a small change in three places in our code. Roughly 1-2 hours including tests. It does change authentication code, so I'd want someone to sign in, sign up, and sign out afterward to confirm nothing broke.

2. The HTTP library used for avatar imports (axios), this week. When a customer imports a profile picture, they give us a URL and our server fetches it. Our version can be tricked into fetching internal addresses — our own machines — and returning what it finds. This is the one where a customer genuinely controls the input, so the attack shape is real rather than theoretical. The fix is an upgrade plus a rule limiting which addresses we're willing to fetch. Roughly 2-3 hours.

3. lodash, whenever. It only runs in a build script that generates our sitemap; no customer request ever touches it. Five-minute upgrade, no breaking changes. Worth doing for tidiness, not for risk.

The remaining sixteen are routine version bumps I'd fold into normal maintenance.

One thing you didn't ask about that I think matters more than any single item above: we have no automated dependency updates configured (no Dependabot or Renovate). That's the reason 23 piled up quietly — nothing tells us when a dependency goes bad, so we learn about it when someone else notices. Setting it up is about an hour.

Two things I need from you: can I take 1-2 hours today for the session-token fix, and do you want the automated-updates tooling set up now or after the three fixes land?
