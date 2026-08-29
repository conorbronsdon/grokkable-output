48 of 61 routes are migrated and passing tests; 9 are blocked and 4 haven't started, and the week deadline is tight if one of those 4 needs a more complex rewrite.

The 9 blocked routes use session middleware that doesn't have a clean Fastify equivalent yet — I built an adapter, but it renews sessions on read instead of on write like Express did, which changes idle-logout behavior. I need your call on whether that's acceptable before I can finish those. The 4 unstarted routes handle file uploads and need a bigger rewrite; I'll size that up tomorrow, but if it needs streaming instead of buffering, that alone is 2-3 days, which puts the week deadline at risk.

Also found two pre-existing bugs, unrelated to the migration: an admin export can silently truncate large files because a write isn't awaited, and the Stripe webhook validates its signature after parsing the body, which is a bit sketchy even if likely benign. Want me to fix those while I'm in there, or file them separately?
