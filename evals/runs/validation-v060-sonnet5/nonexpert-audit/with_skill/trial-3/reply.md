Not great, but manageable — and only two of the 23 issues actually matter.

Here's the real picture. The scanner found 23 problems, which sounds alarming, but most are in developer tools that never touch our live site, so they carry no real risk. Two issues are genuine and worth fixing fast:

Our login system uses a library with a known flaw in how it verifies session tokens. Exploiting it isn't trivial today, but this is the code that decides who's allowed into an account, so we're treating it as urgent. Fix is a version upgrade plus a small code change — about 1-2 hours of engineering work.

Second, the code that imports a user's avatar image fetches whatever URL the user provides, and the library doing that fetch has a flaw that could let someone redirect it to internal systems instead of an image. That's a real exploit path, not just a theoretical one. Fix is a version bump plus adding a check that restricts which URLs it's allowed to fetch — about 2-3 hours.

There's also a small, low-risk item in a build script we'll fix at the same time since it's a five-minute change.

We checked 30 days of error logs for signs either issue has been exploited and found nothing, so this looks like a "fix before it's a problem" situation, not an active breach.

Plan: fix the login issue today, the avatar-fetch issue this week, and roll the other 20 minor items into normal maintenance — they're routine version bumps with no urgency.

One gap worth closing after that: we don't have automated dependency-update checks running, which is how we ended up with 23 items piled up instead of catching them one at a time. Want me to set that up too?
