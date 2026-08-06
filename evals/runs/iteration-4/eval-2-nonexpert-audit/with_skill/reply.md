Much less bad than the headline number, but two things do need fixing this week. The scanner flagged 23 problems in the outside code libraries our app depends on. Three of them actually touch your live app. The other 20 are either in tools that only run on developers' laptops and never ship to customers, or in code that a real user request never reaches.

I also checked 30 days of error logs for the traces these particular attacks leave behind and found nothing. That's reassuring, not proof — absence in logs isn't the same as confirmation nobody tried.

Here are the three that matter, in the order I'd fix them:

- **Login token checking (the `jsonwebtoken` library, in `middleware/auth.ts`).** This is the code that verifies a visitor is really logged in as who they claim. The version we run has a known flaw in how it validates those tokens. Pulling it off would require an attacker to control cryptographic material we don't hand out, so I don't think it's exploitable against us today — but this is the front door of the app, so I'd treat it as real anyway. The fix is a version upgrade plus a one-line change in three places in our code. Roughly 1–2 hours including tests. I'd do this one today.
- **Avatar importing (the `axios` library, in `server/webhooks.ts`).** When a user imports a profile picture, they give us a web address and our server goes and fetches it. The version we run can be tricked into fetching addresses it shouldn't — including internal ones inside our own network. This is the one where the attack actually has a workable shape, because the user genuinely controls the address. The fix is an upgrade plus a list of approved addresses the server is allowed to fetch from. Roughly 2–3 hours. This week.
- **`lodash`, a general utility library.** The scanner rates this one "critical," which is why it looks alarming, but we only use it in a build script that generates our sitemap. It never runs while a customer is using the app. Five-minute upgrade with no risk of breaking anything.

The remaining 20 are routine. I'd roll them into a normal maintenance update rather than treating them as an incident.

One thing worth fixing beyond the code: we have no automated dependency updates configured (no Dependabot or Renovate in the repo). That's the reason 23 of these piled up quietly. Turning it on means these arrive as small weekly pull requests instead of as a scary audit report.

Two questions for you: do you want me to start on the login token fix today and the avatar fix this week? And should I set up automated dependency updates while I'm in there?
