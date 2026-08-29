Short version: not as bad as "23 vulnerabilities" sounds, but two things need real attention this week.

**How bad is it, really**

npm flagged 23 issues. 20 of them don't matter much — they're in dev tools we don't ship, or in code paths nothing user-facing touches. I checked our error logs for the last 30 days for signs anyone's tried to exploit any of this: nothing.

Two things are real:

1. **Our auth library (jsonwebtoken) has a flaw in how it verifies login sessions.** This is the piece that checks "is this person really logged in" on every request. Exploiting it isn't trivial — an attacker would need something we don't currently expose — but it's the auth layer, so I'm not willing to shrug it off.
2. **Our avatar-import feature has a bug (in a library called axios) that could let someone make our server fetch an internal/internal-network URL on their behalf**, since it takes a user-supplied URL. This one's more directly exploitable — someone could actually try it — but it's a lower-value target than the login system.

A third item (lodash, in a build script) is nearly cosmetic — it's not in a live request path — but it's a 5-minute fix so we'll knock it out anyway.

**What we do**

- **Today:** patch the auth library. A few hours of engineering time including tests, since the fix changes how tokens get verified and touches 3 spots in the code.
- **This week:** fix the avatar-import issue and add a restriction so it can only fetch external URLs, not internal ones. Half a day.
- **Next normal maintenance window:** clean up everything else — it's routine version bumps, no urgency.

**One gap worth closing:** we don't have anything auto-flagging new vulnerabilities as they show up (no Dependabot/Renovate). I'd add that once the above is done, so we're not relying on someone telling you about the next one.

Net: this is a normal amount of dependency drift for an app our size, not a five-alarm fire — but the auth fix should happen before anything else this week.
