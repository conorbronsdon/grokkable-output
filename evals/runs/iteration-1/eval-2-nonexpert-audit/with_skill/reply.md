Much less bad than the number sounds, but two of them are real and one sits in our login system. The scan reported 23 vulnerabilities; 20 of those are in tools that only run on our own machines during development, or in code an attacker has no way to reach. Three are worth fixing, and I'd do them in this order:

1. **Session tokens, today.** The library that checks whether a login token is genuine (jsonwebtoken) has a known flaw where a forged token can be accepted under the wrong verification method. Pulling it off requires access to key material we don't hand out, so I'd call this unlikely rather than an emergency — but it's the code that decides who is logged in, and that's not where I want to accept odds. The fix is an upgrade plus a small change at three places in the code that verify tokens. About 1-2 hours including tests.

2. **Avatar imports, this week.** When a user imports an avatar, they hand us a URL and our server goes and fetches it. The version of the HTTP library we use (axios) can be tricked into fetching a different address than the one it appears to be given, including addresses inside our own network. This is the one with a genuinely exploitable shape, because the attacker supplies the input. The fix is an upgrade plus a restriction on which addresses we'll fetch at all. About 2-3 hours.

3. **lodash, whenever.** The scan calls this critical, but we only use it in a build script that generates our sitemap — nothing a customer ever touches. It's a five-minute upgrade with no risk of breaking anything, so it's worth doing for tidiness, not safety.

The remaining 20 are routine and can ride along with normal maintenance.

I also searched 30 days of error logs for traces of these specific attacks and found nothing. That's reassuring, not proof — logs only show what got recorded.

One thing you didn't ask about that I think matters more than any single item above: we have no automated dependency updates configured (no Dependabot or Renovate). That's why 23 advisories piled up rather than getting handled a few at a time. Without it, we'll be back here in six months.

So: do you want me to start the session-token fix today, and set up automated updates while I'm in there?
