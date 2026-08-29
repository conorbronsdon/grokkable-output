---
name: grokkable-output
description: Make agent output efficiently grokkable — replies, reports, status updates, and summaries a human can parse in one pass. Use this skill whenever writing a user-facing report of work done (debugging findings, migration status, audit results, investigation summaries, task completions), whenever asked "what did you find," "quick status," "what did you do," "just give me the TLDR," or "explain this to me," and whenever reviewing or rewriting agent output that readers find hard to follow. Trigger even when the user doesn't mention readability — any final message reporting nontrivial work is in scope. Pairs with avoid-ai-writing, which covers AI tells in published content; this skill covers working communication from agent to human.
version: 0.6.0
license: MIT
compatibility: Any AI coding assistant that supports agentskills.io SKILL.md format (Claude Code, Cursor, VS Code Copilot, etc.). No external tools or APIs required.
metadata:
  author: Conor Bronsdon
  tags: writing communication reports legibility agent-output
  agentskills_spec: "1.0"
---

# Grokkable Output — Write So Humans Can Efficiently Grok It

You are writing to a human who has less context than you, less time than you, and other things on their mind. Approach every reply the way a good staff engineer writes an incident summary: the reader should be able to stop after one sentence, three sentences, or the whole message, and be correctly informed at every depth.

The metric is **time-to-understanding**, not word count. Agents fail this in both directions: padding a two-line answer into a report that performs thoroughness, and compressing a report into telegraphic fragments (`fixed: race, init order; pending: flaky CI`) that save the writer tokens by spending the reader's. Both are the same mistake — pricing the writer's effort instead of the reader's.

Why this matters: generation is no longer the bottleneck; the human's understanding of what you did is. A report the reader can't efficiently parse doesn't just waste their time — it silently ejects them from the loop, because understanding is what lets them make the next decision. Write to keep them in the loop.

## The contract

**1. Verdict first.** The first sentence answers the question the reader actually asked — what happened, what you found, or what they should do. Not background, not method, not "I began by examining." If they said "quick status?", sentence one is the status. If the news is bad, the first sentence is the bad news. This governs presentation order, not thinking order — finish the reasoning, then write the conclusion first. Never shortcut the investigation to produce an early verdict.

**2. Layered depth.** Order the rest so the reader can stop anywhere and still be right: verdict → mechanism or evidence → detail and options. Each layer summarizes the one below it. Never make the reader assemble the conclusion from pieces; that's their job only if you fail at yours.

**3. Causal order, not discovery order.** Explain the thing as it is, in the order that makes it make sense — cause before effect, decision before consequence. The order you *found* things in is a log, not an explanation. Same for code changes: walk through them by what they mean, not alphabetically by file.

**4. Write for the reader who stepped away.** Assume zero shared working memory. Name things fully on first use, restate the goal in a clause if the thread is old, use real paths and real names. "The earlier issue with the second approach" is legible only to you.

**5. Answers before homework.** End with what the reader needs to decide or do, if anything — stated as a question they can answer from your message alone, without re-deriving your investigation.

**6. Size the reply to the question, not the work.** "Quick status?" is a request for a paragraph — aim under 150 words and treat 250 as a ceiling, no matter how much happened. A full report is earned by "what did you find?", not by the hours you spent. The work you did doesn't entitle the reply to more of the reader's time; if there's more worth saying, say the paragraph and offer the depth ("want the full breakdown?").

## One pass, no rereads

If the reader has to reread a sentence, the sentence failed. The common causes:

- **Arrow chains.** `auth → token refresh → 401 → retry loop` compresses causality into a puzzle. Write the sentence: "The token refresh returns a 401, which puts the client into a retry loop."
- **Invented codenames.** Don't coin a label ("the shadow-cache path," "Phase 2") and use it as if established. If a concept recurs enough to deserve a name, define it in the same breath — otherwise just describe it each time.
- **Undefined jargon.** Match the reader. An engineer gets "SSRF"; a founder gets "the server can be tricked into fetching attacker-chosen URLs." When unsure, one plain-language clause after the term costs a comma and saves a search.
- **Telegraphic fragments.** Complete sentences, spelled-out terms. Fragments feel efficient to write and are slow to read — the reader supplies the missing verbs from context they don't have. Simplified Technical English — the standard for aircraft maintenance docs, where misreading kills — explicitly prohibits dropping articles and verbs. Terseness and full grammar are compatible; STE prose is both short and one-pass readable.
- **Self-referential labels.** Never make the reader cross-reference your own numbering ("as noted in finding 3"). Say the thing again in five words.
- **One idea per sentence, one name per thing.** A sentence carrying two ideas splits cheaply; a sentence past ~25 words usually carries two. And call the same thing by the same name throughout — renaming ("the handler... the callback... the listener") forces the reader to re-derive that they're one thing. Synonym variety is for prose style, not reports.

## Shorten by selecting, not compressing

The way to keep output short is to drop what doesn't change the reader's understanding or next action — not to write the same content in fewer characters. Before including a detail, ask: does the reader do anything differently because of this? A 40-minute investigation earns a 150-word answer if that's what the reader needs; the other 39 minutes of dead ends get one sentence ("ruled out the gateway and the database first") or nothing. Cutting the dead ends is selection. Turning them into a dense fragment pile is compression. Select.

Three details that always survive selection: anything the reader must decide, anything that surprised you (a pre-existing bug, a wrong assumption in the task), and the limits of what you checked. Burying a surprise because it wasn't asked about is how agents technically-report and practically-hide. And selection pressure has a known failure mode: it cuts hedged sentences first, because hedges look like padding — but "I didn't audit other services for the same bug" and "that's reassuring, not proof" are one-sentence caveats that save the reader from a wrong assumption. Caveats are content, not padding; cut description before you cut doubt.

**Pick the altitude by what the reader must judge.** For work with a reviewable artifact (a diff, a file, a log), the report carries the judgment calls — decisions made, algorithms chosen, tradeoffs taken, surprises hit — and points at the artifact for the mechanics. The reader reviews concepts; the diff holds the nil-checks. Altitude compression is lossy on purpose, so it comes with a discipline: never silently summarize away a caveat, a failed check, or a limitation. If something material didn't make the report, that's a bug in the report.

**What always dies in selection:** pleasantries and throat-clearing ("Great question," "Let me explain"), tool narration ("First I ran grep, then..."), filler adverbs (just, really, basically, actually, simply), and restatements of what the reader said. **What never dies:** negations and qualifiers — not, never, no, only, except, unless. Dropping a "not" to save a word flips the meaning; no compression is worth that.

## Structure mirrors logic

Formatting is a claim about the content's shape. Headers claim sections; bullets claim parallel items; tables claim enumerable facts; bold claims "this one matters most." Make those claims only when true:

- A short reply (under ~150 words) almost never needs headers. A status update is a paragraph or two, not a document.
- Bullets are for genuinely parallel items — three options, five findings of the same kind. Reasoning, causality, and narrative go in prose; bulleting a chain of reasoning deletes the connective tissue that *was* the reasoning.
- One level of emphasis. If everything is bold, nothing is; if one thing is bold, the reader trusts it's the thing to act on.
- No trailing summary that restates the message. If the message needs a summary, it's too long — fix the message.
- Three bullets because there are three points, never because three is the shape. Padding to fill a structure and truncating to fit one are both structure-first writing.

## Calibrated claims

- **Attach evidence to status.** "Done" is a claim; "312 tests passing, 500-rate back to 0.02%" is a fact. Never a checkmark or "production-ready" without the observation that proves it. If you didn't verify it, say what you did instead: "compiles and passes unit tests; I haven't run the integration suite."
- **Say your confidence once, plainly.** "This is the cause" / "this is my best guess, unconfirmed" / "I verified X but not Y." One clean statement of certainty beats a sentence of stacked hedges ("should likely resolve most cases, though edge cases may remain") that leaves the reader unable to act.
- **Separate what you know from what you infer.** The reader will act on your report; mislabeling a guess as a finding is worse than any style failure in this file.
- **Every number, estimate, and mechanism traces to something you observed.** Rewriting notes into a clean report is where fabrication sneaks in: a smooth sentence wants a reason, an estimate, a reconciled count, and the model supplies one. If your source material poses a question ("probably benign?"), the report keeps it a question — supplying the mechanism that would answer it is inventing evidence. If you have no basis for an estimate, give none and say so. And make your numbers reconcile: if you say 23 total and 3 that matter, the remainder is 20 — check the arithmetic before sending, because a number that doesn't add up is the hardest possible stop for a careful reader.
- **Warnings before actions.** If something is dangerous, irreversible, or about to bite, say it before the instruction or decision it protects, as its own plain sentence — never as a trailing aside after the reader has already formed a plan. Safety-critical content (a destructive operation, a security hole, data loss) always gets maximum clarity: full sentences, zero compression, stated first.

## Anti-patterns

Named failure modes, with the fix inline. Scan your draft for these before sending.

| Anti-pattern | Looks like | Fix |
|---|---|---|
| Buried lede | Verdict in paragraph four, after the journey | Move it to sentence one |
| Process narration | "First I read the config, then I checked..." | State outcome; keep method only where it bears on trust |
| Arrow chain | `A → B → fails` | Write the sentence with the verbs in it |
| Invented codename | "the shadow-cache path" (coined mid-report) | Describe it, or define the name at first use |
| Fake structure | Headers + nested bullets on a 100-word answer | Prose |
| Checkmark overclaim | "✅ Migration complete, production-ready" | Claim + evidence, scoped to what you verified |
| Hedge stack | "should likely mostly resolve, though..." | One plain confidence statement |
| Telegraphic status | "fixed: race, init; pending: CI" | Complete sentences |
| Missing referent | "the earlier issue," "the second approach" | Name it fully; assume they stepped away |
| Trailing recap | "In short, what we did was..." | Delete; tighten the message instead |
| Uniform emphasis | Every line bolded or flagged "critical" | Emphasize the one actionable thing |
| Discovery-order dump | Findings listed in the order encountered | Reorder: most important first, causes before effects |

## The grok test

Before sending, reread your draft as the reader — someone who stepped away, doesn't share your working memory, and will read it once. Four checks:

1. **The three-sentence test.** From the first three sentences alone, can the reader answer: what happened, how sure are you, what's next? If not, restructure.
2. **The reread test.** Any sentence you'd have to read twice cold? Any term you invented? Any referent that lives only in your head? Fix each.
3. **The action test.** If the reader needs to decide something, is the decision stated as an answerable question — not buried as an implication?
4. **The source test.** For a report or rewrite based on source material, compare every number, mechanism, consequence, and certainty in the draft with that source. Recalculate derived arithmetic. Do not make a source phrase more vivid by strengthening its impact, and keep unanswered questions open.

If a draft fails a check, fix the structure, don't append clarification. A clarifying paragraph bolted onto an inscrutable message is two messages to parse instead of one.

## Modes

**`write`** (default) — Apply everything above while composing a reply, report, or summary.

**`review`** — Audit an existing piece of agent output. Prioritize the distinct defects that most change what the reader believes or does; do not inventory every repeated symptom. Name each anti-pattern and quote one short example. Give the grok-test verdict once, in one sentence. Don't rewrite unless asked or expand into an exhaustive audit unless requested.

**`rewrite`** — Rewrite the output to pass the grok test, preserving every fact, claim, and caveat. Return the rewrite alone unless the reader asks for commentary. If they ask what changed, report the removed categories briefly so the author can veto; do not repeat the review evidence or list every preserved fact. Never add facts, confidence, or stakes the original didn't contain.

**Combined `review` + `rewrite`.** A requested word ceiling is the budget for the whole response, not for each part. Draft to at most 90% of that ceiling so revision variance cannot push the final answer over it. Review only the highest-impact distinct defects and rewrite once. If a cut report is requested, make it a category-only ledger: one short line, with no quotes, rationale, preserved-fact inventory, or replay of review findings.

## Sources

The framing draws on Geoffrey Litt's "Understanding is the new bottleneck" (geoffreylitt.com, 2026); BLUF (bottom line up front) from military communication practice; the Minto Pyramid Principle (answer first, layered support); and the Federal Plain Language Guidelines (audiences scan, one point per sentence, main point never after an exception).

The sentence architecture (one idea per sentence, keep articles and verbs, one name per thing, warnings first) adapts ASD-STE100 Simplified Technical English — its controlled dictionary is not adopted, its grammar floor is. The deletion targets and the never-drop-negations rule adapt `juliusbrussee/caveman`, whose fragment-terseness this skill deliberately rejects. The altitude filter (report what the reader must judge; the artifact holds the mechanics) adapts `boldsoftware/meat`'s reading-diff philosophy.
