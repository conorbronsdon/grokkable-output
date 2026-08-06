<div align="center">

# grokkable-output

**Make your agent's replies parseable in one pass — verdict first, no decoding required.**

[![GitHub stars](https://img.shields.io/github/stars/conorbronsdon/grokkable-output?style=social)](https://github.com/conorbronsdon/grokkable-output/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![X](https://img.shields.io/badge/X-@ConorBronsdon-1DA1F2?logo=x)](https://x.com/ConorBronsdon)

</div>

A portable skill ([SKILL.md](SKILL.md)) for Claude Code, Cursor, OpenClaw, Codex, and any agent that reads the [agentskills.io](https://agentskills.io) format. It changes how an agent writes its replies, reports, and status updates: the answer arrives in the first sentence, causality reads as sentences instead of `A → B → fails` chains, structure appears only when the content has that shape, and every number traces to something the agent observed.

Models are rewarded for looking thorough; this skill makes them optimize for your parse time instead — a prompt-layer fix for an incentive problem.

## Quick demo

The same agent, same debugging notes, answering "ok what did you find?"

**Without the skill** — 371 words, four section headers, and the mechanism delivered as an arrow chain:

> sandbox host → Avalara 429s → each 429 retried 3x with 2s backoff (up to +6s latency) → tax-svc p99 goes 210ms → 8.4s → blows past payment-orchestrator's 5s downstream timeout → `TaxLookupTimeout` → checkout-svc catches it as a generic `Exception` and rethrows as a 500.

**With the skill** — 288 words, no headers, verdict in sentence one:

> The checkout 500s came from tax-svc v2.14.0, which shipped pointing at the Avalara *sandbox* endpoint instead of prod. I rolled tax-svc back to v2.13.2 at 15:12 UTC [...] The 500 rate was back to baseline (0.02%) by 15:19.

What changed:

- The verdict — root cause, already fixed — moves to sentence one
- The arrow chain becomes sentences with the verbs in them
- Four bold headers on a chat-length reply become short paragraphs
- 371 words → 288, cut by dropping detail that doesn't change the reader's next move, not by compressing grammar
- The reply ends with the one decision the engineer needs to make, stated as an answerable question

Both replies are factually correct. One of them you read once. Full unedited pairs, with the input notes they were written from, in [`examples/`](examples/).

## What it teaches the agent

- **Verdict first, layered depth.** The first sentence answers the question asked. The reader can stop after one sentence, three, or the whole message and be correctly informed at every depth.
- **One pass, no rereads.** No arrow chains, no invented codenames, no undefined jargon, no telegraphic fragments. If a sentence needs rereading, the sentence failed.
- **Shorten by selecting, not compressing.** Drop what doesn't change the reader's understanding or next action; never crush the rest into fragments. Caveats are content, not padding — they survive selection.
- **Structure mirrors logic.** Headers, bullets, and bold are claims about the content's shape; make them only when true. A quick status is a paragraph, not a document.
- **Calibrated claims.** Status carries its evidence, confidence is stated once and plainly, and every number, estimate, and mechanism traces to something observed. Open questions stay open.
- **Size the reply to the question.** "Quick status?" earns a paragraph no matter how much work happened.

Three modes: `write` (default — compose replies this way), `review` (audit an existing output, flag anti-patterns by name), `rewrite` (fix an output, preserving every fact and caveat).

## Why a skill, not just "be concise"

"Be concise" makes agents cut the wrong things — models under length pressure drop caveats and qualifiers first because hedges look like padding, while keeping their most confident claims. This skill targets *parse cost*, not word count: it names 12 specific anti-patterns (buried lede, process narration, checkmark overclaiming, fake structure, hedge stacks...), explains why each fails, and ends with a three-check self-test the agent runs before sending. In A/B testing the with-skill replies were usually shorter — but by selection, not compression.

## Testing

Tested A/B on Opus subagents: three scenarios (a production debug report, a mid-migration "quick status?", a dependency audit explained to a non-engineer), identical input notes, with and without the skill, graded against per-scenario assertion sets by an independent model instance — including a fidelity pass checking every number and mechanism against the input notes.

Final round: 21/22 assertions with the skill vs 15/19 baseline on the original set. Every baseline failure was structural: arrow-chain causality, bold section headers on chat-length replies, a trailing recap restating the message. One known limitation is documented honestly: in one scenario the with-skill reply invented an effort estimate the notes didn't contain; the skill's trace-every-number rule narrowed but has not fully closed that failure class. The before/after pairs in [`examples/`](examples/) are unedited outputs from these runs, chosen from the scenarios that passed the fidelity check.

## Installation

**Claude Code** — clone as a skill:

```bash
git clone https://github.com/conorbronsdon/grokkable-output ~/.claude/skills/grokkable-output
```

Or download just [`SKILL.md`](SKILL.md) and reference it from your `CLAUDE.md`. To invoke on demand, add a slash command at `~/.claude/commands/grokkable.md` that points at the skill file.

**skills.sh:**

```bash
npx skills add https://github.com/conorbronsdon/grokkable-output --skill grokkable-output
```

**OpenClaw** — clone to `~/.openclaw/skills/grokkable-output`.

**OpenAI Codex** — place at `.agents/skills/grokkable-output/SKILL.md` (project) or `~/.agents/skills/` (global).

**Cursor / Windsurf / Cline / Copilot** — paste `SKILL.md` into `.cursor/rules/`, `.windsurf/rules/`, `.clinerules/`, or `.github/copilot-instructions.md` respectively.

**Claude.ai Projects / custom GPTs** — paste `SKILL.md` into the project or GPT instructions.

## The problem in the wild

This isn't one person's pet peeve. The complaints repeat everywhere agent output gets read:

- *"It explains the test framework, restates the task, writes a 'I will' paragraph, and only then says which file changed."* — [knightli.com](https://knightli.com/en/2026/07/10/claude-code-reduce-verbose-output-settings) on Claude Code defaults
- *"I find all coding agents to be verbose, even with explicit instructions to reduce verbosity."* — recurring Hacker News sentiment; others note Claude's *"overly verbose 'walls of text' comments"* are how they spot its code
- Geoffrey Litt's [thesis](https://www.geoffreylitt.com/2026/07/02/understanding-is-the-new-bottleneck): *"reading is hard work"* — agents produce faster than humans can understand, and raw output order (alphabetical diffs, discovery-order reports) doesn't match how a person builds understanding

The common home-grown fixes — "result first" CLAUDE.md rules, fixed report schemas (changed files → behavior → validation → risks), per-item length caps, banned-phrase lists — are all fragments of the same missing skill. This repo is that skill in one portable file, tested rather than vibes-tuned.

One caveat from those discussions is built in: verdict-first governs *presentation* order, not thinking order. The skill tells the agent to finish its reasoning, then write the conclusion first — not to shortcut the investigation.

## Related work

The ecosystem attacks adjacent problems; none of these covers verdict-first analytical reports, which is the niche this skill fills.

| Skill | What it does | How this differs |
|---|---|---|
| [i-have-adhd](https://github.com/ayghri/i-have-adhd) | Reorders output for ADHD readers: lead with the *action*, step counters, capped lists, a pre-send deletion checklist | Action-first for task execution; grokkable-output is verdict-first for findings and reports — "here's the judgment, the confidence, and what would change it" |
| [caveman](https://github.com/JuliusBrussee/caveman) | Compresses output ~65% by dropping articles and filler; excellent preservation rules (negations, numbers, code) | Optimizes token cost, not comprehension — it explicitly doesn't reorder, so a buried verdict stays buried, just shorter. We borrow its deletion targets and negation rule, reject its fragments |
| [BuilderIO /quick-recap](https://github.com/BuilderIO/skills) | Ends every completion with a green/yellow/red work-state signal | The ecosystem's one verdict primitive — placed at the end. This skill puts the verdict in sentence one |
| [agent-style](https://github.com/yzhao062/agent-style) | 21 prose-mechanics rules (Strunk/Orwell/Pinker + observed LLM failures) with an audit CLI | Word- and sentence-level style; explicitly no coverage of argument structure or claim positioning |
| [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | Removes AI tells from published content (60+ patterns, detector, corpus-tested) | Sibling project, same author. Published prose vs. working communication; the two compose |

## When not to use it

This skill governs working communication from agent to human — replies, reports, status updates. For removing AI tells from *published content* (essays, posts, docs), use its sibling [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing); the two compose. And if you want maximum token compression at the cost of grammar, that's [caveman](https://github.com/juliusbrussee/caveman)'s trade, deliberately not this one — Simplified Technical English prohibits telegraphic writing for a reason: fragments save the writer tokens by spending the reader's attention.

## Credits

The framing draws on Geoffrey Litt's ["Understanding is the new bottleneck"](https://www.geoffreylitt.com/2026/07/02/understanding-is-the-new-bottleneck); BLUF and the Minto Pyramid Principle; the [Federal Plain Language Guidelines](https://www.plainlanguage.gov/); ASD-STE100 Simplified Technical English (sentence architecture, not the controlled dictionary); [juliusbrussee/caveman](https://github.com/juliusbrussee/caveman) (deletion targets and the never-drop-negations rule); [boldsoftware/meat](https://github.com/boldsoftware/meat) (report what the reader must judge; the artifact holds the mechanics); and [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (paragraph discipline — reducing reading load is about reordering and breaking text at thought boundaries, not just shortening it).

## About

Built by [Conor Bronsdon](https://conorbronsdon.com?utm_source=github&utm_medium=referral&utm_campaign=repo-readme&utm_content=grokkable-output) — host of [Chain of Thought](https://www.youtube.com/@ChainofThoughtPod?utm_source=github&utm_medium=referral&utm_campaign=repo-readme&utm_content=grokkable-output) · [GitHub](https://github.com/conorbronsdon) · [X](https://x.com/ConorBronsdon) · [LinkedIn](https://www.linkedin.com/in/conorbronsdon/)

---

## Disclaimer

*This is an independent personal project, not affiliated with, sponsored by, or endorsed by any company. All views expressed are my own.*

## License

[MIT](LICENSE)
