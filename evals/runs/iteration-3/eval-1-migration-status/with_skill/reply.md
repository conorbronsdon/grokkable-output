48 of the 61 route handlers are on Fastify with 312 tests passing. The remaining 13 are both waiting on decisions from you, and the week deadline is tight.

Nine routes are blocked on sessions. Our store is connect-redis v6, which is Express-only, so I wrote a 40-line Redis adapter for @fastify/session. It passes 3 of the 4 session tests; the failure is renewal semantics, because the Fastify plugin renews a session on read while Express renewed on write. Is a 30-minute idle logout that renews on read acceptable? If not, I'll keep those nine on Express behind a proxy until we swap the store.

The four file-upload routes haven't started. Moving from multer to @fastify/multipart is a real rewrite: roughly a day if we buffer uploads, two to three days if we stream them. That choice is what decides whether the week holds — which do you want?

Separately, I hit two pre-existing bugs that the migration didn't cause. routes/admin/export.js never awaits the CSV write, so exports over 10MB truncate silently (I reproduced it). And routes/webhooks/stripe.js validates the Stripe signature after parsing the JSON body; I haven't worked out whether that's actually exploitable.
