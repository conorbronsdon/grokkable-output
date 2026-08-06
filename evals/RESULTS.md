# grokkable-output — eval results (iterations 1-5, 2026-08-06)

All runs on Opus subagents given the same fixture notes (`fixtures/`) and user
question. Full replies and per-assertion grading with verbatim evidence quotes in
`runs/`. Iterations 2-3 graded by independent Opus subagents, not the skill author.

## Scores

| Round | Skill version | Config | Score | Notes |
|---|---|---|---|---|
| iter-1 | v0.1.0 | with_skill | 19/19 (100%) | author-graded |
| iter-1 | — | without_skill | 15/19 (78.6%) | author-graded |
| iter-2 | v0.2.0 | with_skill | 18/19 (94.7%) | independent grader |
| iter-3 | v0.3.0 | with_skill | **21/22 (95.5%)** | independent grader, harder set (+fidelity assertion) — SHIP; v0.3.1 (presentation-order patch) is the shipped public version |
| iter-4 | v0.4.0 | with_skill | 22/25 (88%) | independent grader — DON'T SHIP |
| iter-5 | v0.5.0 | with_skill | 24/28 (86%) | independent grader, harder set again — DON'T SHIP |

## What each round found

**Iter-1 (v0.1 vs no skill).** Opus baselines already handle content (verdict-first,
decisions surfaced, jargon translated). Every baseline failure was structural: a
literal arrow chain plus four bold headers on a 371-word chat reply (eval-0), three
pseudo-headers on a "quick status?" (eval-1), six headers plus a trailing "Proposed
plan" recap at 464 words (eval-2). The skill's measured value is chat-register
structure discipline.

**Iter-2 (v0.2, independent review).** Verdict: don't ship. Outputs grew ~8%;
selection pressure cut caveats asymmetrically ("that's reassuring, not proof"
dropped); 4 of 6 with-skill outputs across iters 1-2 contained unsupported claims —
an invented mechanism answering the fixture's open Stripe question, an invented
Dependabot estimate, and "the remaining sixteen" against a true remainder of 20.
Root cause: the anti-fabrication rule lived only in `rewrite` mode. Full review:
`independent-review-v0.2.md`.

**Iter-3 (v0.3, validation).** Ship verdict. Proportionality fixed (eval-1: 328 →
193 words, 57 under the ceiling); caveats now stronger than any prior version
(eval-0 adds an unprompted scope-limit line; eval-1 keeps the Stripe question open);
arithmetic reconciles. Word counts 288/193/437.

## Known open defect (v0.4 target)

The fabricated-estimate class is narrowed but not closed: v0.3 eval-2 still says
Dependabot setup "is under an hour" — no basis in the fixture, same claim v0.2
invented. One of four fidelity sub-properties failed; the other three (sourced
numbers, open questions kept open, reconciling arithmetic) now pass.

## Eval-suite debt (from the independent grader)

- eval-2 and eval-0 have no length ceiling; eval-2 grew to 437 words uncaught
  (grader suggests ~350 for eval-2).
- The fidelity assertion bundles four properties into one pass/fail — a fix of
  three and break of one collapses to FAIL. Split it.
- n=1 per cell throughout; no variance measurement.
- One eval-2 structure assertion was added after iter-1 outputs were seen (marked
  `[added post-run]`).

## Iterations 4-5: the meta-finding

v0.4.0 (paragraph discipline) and v0.5.0 (i-have-adhd adoptions + counter-fixes)
both failed independent validation. Each round's targeted fixes worked — v0.5
fixed bullet density, didn't repeat the translation-strength bug, restored four
of five v0.4 content losses — but each round also produced fresh defects
elsewhere: invented impact claims, a scope statement reworded into inaccuracy,
the Dependabot estimate returning, and "Want the full breakdown?" sitting
verbatim in the decision slot two rounds running despite a rule written
specifically against it.

Across five iterations the per-run defect count is roughly constant (~2-4),
redistributed rather than eliminated. Two conclusions for v0.6:

1. **n=1 per cell can't separate rule effects from run variance.** Minimum n=3
   before attributing any change to a rule.
2. **Rule-stacking has hit its ceiling.** The next lever is architectural: a
   two-pass write-then-self-audit flow (the grok test exists but plainly isn't
   being executed as a checklist), and/or a mechanical post-hoc lint for the
   detectable failures (block size, decision-slot content, unsourced estimates).

The shipped skill is v0.3.1. v0.4.0 and v0.5.0 were never released; their full
graded outputs are in runs/iteration-4/ and runs/iteration-5/.
