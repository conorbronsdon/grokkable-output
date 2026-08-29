48 of 61 routes are migrated and passing tests (312 passing). 9 are blocked on session handling, 4 haven't been started.

The 9 blocked routes use express-session with connect-redis, which doesn't support Fastify. I wrote a Fastify session adapter that passes 3 of 4 tests — the failure is a real behavior difference, not a bug: Fastify's plugin renews the session on read, Express renewed on write, so idle-logout timing would change. I need your call on whether that's acceptable before I finish these.

The 4 file-upload routes (multer → @fastify/multipart) haven't started. This is the deadline risk: buffering mode is a 1-day port, but if we need streaming semantics to match current behavior, it's 2-3 days.

Also found two pre-existing bugs, unrelated to the migration: `routes/admin/export.js` doesn't await the CSV write, so large exports (>10MB) get silently truncated. And `routes/webhooks/stripe.js` checks the signature after parsing the JSON body — I think that's benign but haven't confirmed it isn't exploitable.

What I need from you: is renewal-on-read (vs. renewal-on-write) an acceptable change to session idle-logout behavior? That decision unblocks the 9 session routes; I'll move on to the multer routes tomorrow either way.
