# Examples

Real, unedited outputs from A/B testing the skill on Opus subagents. Each example
directory has three files:

- `input-notes.md` — the raw working notes the agent had (the fixture)
- `before.md` — the agent's reply **without** the skill
- `after.md` — the agent's reply **with** the skill

The user question and the notes are identical in both runs; only the skill differs.

## debug-report

A senior engineer stepped away during a production investigation and came back
asking "ok what did you find?"

The before is correct and complete — and costs extra passes to parse: the causal
mechanism is an arrow chain (`sandbox host → Avalara 429s → ... → rethrows as a
500`), and a 371-word chat reply is sectioned by four bold headers. The after says
what happened, why, and what needs deciding, in prose, in 288 words — and adds a
scope-limit caveat ("I only traced the checkout path") that the before buried in
its final bullet.

## quick-status

Mid-migration, the user asks "quick status?"

The before answers a quick question with a formatted document: three bold
pseudo-headers, 273 words. The after is 193 words of prose that opens with the
state (48 of 61 routes, deadline tight), surfaces the two decisions blocking
progress as answerable questions, and keeps an open question open ("I haven't
worked out whether that's actually exploitable") instead of inventing an answer.

## Provenance

Before replies: baseline runs from iteration 1; after replies: v0.3.0 runs from
iteration 3. Graded by an independent model instance against per-scenario
assertion sets, including a fidelity check that every number and mechanism traces
to the input notes. The full eval corpus (three scenarios, three iterations,
per-assertion grading with verbatim evidence) lives with the skill's development
history.
