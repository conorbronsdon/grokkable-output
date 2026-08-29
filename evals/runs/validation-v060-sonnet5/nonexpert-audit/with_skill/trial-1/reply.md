Not bad, and nothing's actively being exploited — but two things need fixing this week.

Here's the real picture. The scanner flagged 23 issues, but 20 of those are noise: dev tools we don't ship, or libraries that never touch a real request. I checked 30 days of logs for signs of attack — nothing. Only three things actually matter.

**Fix today:** our login system (jsonwebtoken) has a flaw that, in the wrong conditions, could let someone forge a session token. We don't think we're exposed to the exact attack path, but this is the auth layer, so we're treating it as real. The fix is about 1-2 hours of engineering work, including tests.

**Fix this week:** our avatar-import feature (axios) lets a user supply a URL, and a flaw in that library means a malicious URL could make our server fetch internal resources it shouldn't. This one is actually exploitable in its current shape. Fix is 2-3 hours: upgrade the library and add a check that only allows safe URLs.

**Fix whenever, low stakes:** a third library (lodash) has a known flaw, but it's only used in an internal build script, never in a live request — so real risk is low. Five-minute fix, just good hygiene.

The other 20 advisories are standard version bumps we can roll into normal maintenance.

One gap worth closing separately: we don't have automated dependency updates (Dependabot or similar) running, which is how we ended up with 23 unpatched advisories in the first place. Want me to set that up so this doesn't pile up again?
