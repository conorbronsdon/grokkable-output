Not great, but fixable, and only two things actually matter.

The scary number is 23 vulnerabilities, but 20 of those are noise — dev tools that never ship to production, or minor issues buried deep in dependencies we don't touch directly. I checked our logs for the last 30 days and found no sign anyone has exploited anything.

Two real issues need fixing:

1. **Our login/session system (jsonwebtoken)** has a flaw in how it verifies who's logged in. We're not directly exposed today, but this is the auth layer, so I'm treating it as a real risk rather than a theoretical one. Fix today: about 1-2 hours of engineering work, including a small code change and tests.
2. **Our avatar-import feature (axios)** lets a user supply a URL, and a bug there means that URL isn't being checked carefully enough — someone could potentially use it to probe internal systems. This one's exploitable in a straightforward way. Fix this week: about 2-3 hours, adding a proper allowlist for URLs.

There's also a low-risk item (an old lodash version) that's only used in an internal build script, not in anything customer-facing — five-minute fix, no rush, just hygiene.

Everything else — the other 20 advisories — gets cleaned up in a normal maintenance pass, no urgency.

One gap worth closing: we don't have automated dependency update checks (tools like Dependabot) running on this repo, which is how we ended up needing a manual audit instead of catching this incrementally. Worth setting up so this doesn't require a fire drill next time.

**What I need from you:** okay to have engineering fix #1 today and #2 this week, in that order?
