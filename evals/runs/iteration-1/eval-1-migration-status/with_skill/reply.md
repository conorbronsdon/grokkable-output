48 of the 61 Express route handlers are migrated to Fastify and passing their existing tests — 312 green from `npm test -- --grep routes`. The remaining 13 split into two groups, and one of them needs a decision from you before I can finish it.

Nine routes are blocked on session middleware. Fastify's session plugin can't talk to our session store, connect-redis v6, which is Express-only, so I wrote a 40-line adapter shim. It passes 3 of the 4 session tests. The failure is renewal timing: Express renewed a session on write, the Fastify plugin renews on read. So the question for you is whether renewal-on-read is acceptable for our 30-minute idle logout — a user who only reads stays logged in indefinitely. If that's fine, I finish these nine tomorrow. If it isn't, I hold them on Express behind a proxy until we swap the store.

The other four are the file-upload routes, where multer becomes @fastify/multipart and the multipart semantics differ. Buffering uploads is roughly a day of work; true streaming is two to three days, and that's the thing that makes the week deadline tight. I'd start those right after the session decision.

Two pre-existing bugs surfaced during the migration, neither caused by it, and I've fixed neither. `routes/admin/export.js` never awaits the CSV write, so large exports truncate silently — I reproduced it above 10MB. `routes/webhooks/stripe.js` validates the Stripe signature after parsing the JSON body; I suspect it's benign, but I haven't proven there's no bypass when the parse throws first. Tell me if you want either patched now.

One sidenote to discount: migrated routes benchmark about 2.1x Express's requests/sec, but that's a hello-world synthetic, not our traffic.
