48 of 61 route handlers are migrated and passing (312 tests green). 9 are blocked on a session-store incompatibility, 4 haven't been started, and the week deadline is at risk if one of those 4 needs a bigger rewrite than expected.

The 9 blocked routes use express-session with connect-redis, which doesn't have a Fastify equivalent. I wrote a Fastify session adapter (40 lines) that passes 3 of 4 tests — the failing one is a real behavior difference: Fastify's plugin renews the session on read, Express renews on write, so idle-timeout logout would fire at a different point. I need your call on whether renew-on-read is acceptable before I can close these out.

The 4 not-started routes handle file uploads and need to move from multer to @fastify/multipart, which isn't a drop-in swap — buffering mode is about a day of work, but if we need streaming (for large uploads) it's 2-3 days, which would blow the week deadline. I'll scope that tomorrow after the session decision.

Also found two pre-existing bugs, unrelated to the migration, while going through this code: the CSV export in admin/export.js doesn't await its write and silently truncates on exports over 10MB, and the Stripe webhook handler checks the signature after parsing the JSON body, which is a bit sketchy even though it's likely benign. Want me to fix those now or file them separately?
