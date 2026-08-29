Not bad, and nothing's been exploited. Three things actually matter; the other 20 are noise.

**What's real:**
1. **Our login system** uses a library with a known flaw (jsonwebtoken). No evidence anyone's exploited it, but it's the code that verifies who's logged in, so we're fixing it today. About 1-2 hours of engineering work.
2. **Avatar imports** — the feature where users paste a URL for their profile photo — uses a flawed library (axios) in a way that's actually exploitable: a user-controlled URL. Fixing this week. 2-3 hours.
3. Everything else is dev tools that never touch production, or code paths nothing malicious can reach. One is a build script no user traffic touches — a 5-minute version bump for hygiene, not urgency.

The "23 vulnerabilities" number you may have heard is mostly that low-risk noise. I checked 30 days of error logs for signs of anyone having exploited any of this — nothing.

**What we're doing:** #1 today, #2 this week, everything else folded into normal maintenance. I'll also set up automated dependency alerts (we don't have any right now, which is how this pile built up) so we catch the next one before it's 23 items deep.

No decision needed from you — just flagging it's handled and you're not exposed right now.
