Not great, but manageable, and only two things actually need fixing this week.

Of the 23 flagged issues, 20 are noise — either dev-only tools that never ship to production, or minor library updates with no real exposure. That leaves 2 real problems and 1 hygiene fix:

**Fix today: the login system.** The library that verifies user sessions (jsonwebtoken) has a known weakness. We don't see a working attack path for it right now, and 30 days of logs show no sign anyone's tried, but it sits in the login flow, so it gets fixed on the assumption it matters. Update plus tests: 1-2 hours.

**Fix this week: the avatar upload feature.** When a user imports a profile picture from a URL, our server fetches that URL. A library we use for that (axios) has a bug that could let someone point our server at internal systems instead of an image — and because this feature does let users control the URL, this one is realistically exploitable, not just theoretical. Fix plus a safeguard limiting which URLs we'll fetch: 2-3 hours.

**Everything else** — including the one other "critical" advisory (a build-script tool, not customer-facing) — rolls into a normal maintenance update. No urgency.

One gap worth closing separately: we don't have automated dependency update tooling (like Dependabot) running, which is how a list like this quietly grows to 23 items instead of getting handled one at a time. Setting that up prevents this from recurring; it's not urgent on its own.

Bottom line: budget half a day of engineering time this week for the two real fixes, then treat the rest as routine.
