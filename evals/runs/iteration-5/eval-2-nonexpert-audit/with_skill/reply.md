Not as bad as the headline number, but two things need doing this week. The scanner flagged 23 vulnerabilities; 3 of them actually matter. The other 20 are either in tools that only run on our own machines while we build the app (never shipped to customers) or in code your app doesn't run. Total fix time for the three: roughly 3-5 hours of engineering.

Here's the order I'd do them in.

**1. jsonwebtoken — today, 1-2 hours.** This library checks that a logged-in user's session token is genuine, so it sits in front of every request. The flaw lets a specially crafted token get accepted under the wrong verification method. Pulling it off would require key material we don't expose to anyone, so I don't believe it's exploitable against us as we're configured — but this is the login layer, so I'd treat it as real rather than theoretical. The upgrade is a breaking change: three places in the code need a new setting added, plus testing.

**2. axios — this week, 2-3 hours.** Our avatar-import feature fetches an image from a URL the user supplies. The version we're running can be tricked into fetching an address the attacker chooses instead, including internal systems that shouldn't be reachable from the outside. Of the three, this is the one with a genuinely exploitable shape, because the user already controls the URL. Fix is the upgrade plus a list of destinations we allow.

**3. lodash — 5 minutes.** The scanner rates it critical, but we only use it in a build script that generates the sitemap, never in a live customer request. Real exposure is low. Worth bumping because it's free and non-breaking.

Everything else rides along in a normal maintenance update.

I searched 30 days of error logs for traces of those two attacks and found none. That's reassuring, not proof — it was a signature search over one log source, not a full investigation.

One separate gap: we have no automated dependency updates configured (no Dependabot or Renovate in the repo), so nothing tells us when a package needs patching. Setting one up is about an hour.

Two things I need from you: do I start the jsonwebtoken fix today, and do you want me to set up automated dependency updates while I'm in there? Happy to send the full list of all 23 with CVE numbers if whoever does the work wants it.
