48 of 61 routes are migrated and passing (312 tests green); the rest is blocked on two decisions rather than raw work.

9 routes are stuck on session handling: our Redis session store only supports Express, so I wrote a Fastify adapter (40 lines) that passes 3 of 4 tests — the failure is that Fastify's session plugin renews the 30-minute idle timer on read, while Express renewed on write. I need you to say whether renew-on-read is acceptable before I ship it; if not, I'll hold those 9 routes on Express behind a proxy until we swap the store.

4 file-upload routes haven't been started. Multer to Fastify's multipart is a bigger rewrite — buffering mode is about a day, true streaming is 2-3 days, and that gap is what could make the week deadline tight.

Along the way I also found two pre-existing bugs, unrelated to the migration: `routes/admin/export.js` doesn't await its CSV write, so large exports (>10MB) can silently truncate; and `routes/webhooks/stripe.js` checks the Stripe signature after parsing the JSON body, which is a potential validation-bypass ordering issue, though I haven't confirmed it's exploitable.

What I need from you: is renew-on-read acceptable for session timeout? That decision unblocks the 9 session routes tomorrow, then I move to the upload routes.
