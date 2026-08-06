48 of the 61 routes are migrated to Fastify and passing their existing tests (312 passing under `npm test -- --grep routes`). Nine are blocked on sessions, and the four file-upload routes haven't started.

One decision from you unblocks the nine: the Fastify session plugin renews a session on read, where Express renewed on write, so the redis adapter shim I wrote passes 3 of the 4 session tests. Is renewal-on-read acceptable for the 30-minute idle logout? If not, I'll hold those nine routes on Express behind a proxy until we swap the store.

Two pre-existing bugs turned up, neither caused by the migration: `routes/admin/export.js` never awaits the CSV write (silent truncation above 10MB, reproduced), and `routes/webhooks/stripe.js` validates the signature after parsing the JSON body — I haven't determined whether that's actually exploitable.

Deadline risk: the four upload routes are about 1 day if we buffer multipart, 2-3 days if we need streaming. Want the full breakdown?
