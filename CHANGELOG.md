# Changelog

## Unreleased

- Added an experimental post-hoc output linter with structured CLI output,
  severity thresholds, positive/complement controls, and Python 3.11/3.13 CI.
  The validated `SKILL.md` remains unchanged at v0.3.1 pending fresh evals.
- Added the versioned v2 evaluation suite and reproducible Claude/Hermes
  harness: four scenarios cover write, review, and rewrite modes; fidelity is
  split into independently graded properties; length ceilings are deterministic;
  and fresh cells require three trials per configuration.
- Archived the first v2 run: 24 fresh Sonnet replies, raw Inkling grades with
  exact session IDs, separate Claude adjudication, and primary verification.
  Write-mode semantic passes improved from 62/78 to 77/78, but all three
  with-skill review/rewrite replies exceeded the 500-word ceiling.

## 0.3.1 — 2026-08-06

- Scoped verdict-first explicitly to presentation order, not thinking order —
  finish the reasoning, then write the conclusion first. Addresses a real
  concern from community discussion that answer-first prompts can shortcut
  reasoning when applied to the process instead of the report.

## 0.3.0 — 2026-08-06

Fixes from an independent model review of v0.2.0 outputs:

- Anti-fabrication promoted from `rewrite` mode into core Calibrated claims:
  every number, estimate, and mechanism traces to something observed; open
  questions stay open; arithmetic must reconcile.
- Caveats declared content-not-padding: selection pressure was cutting
  limit-of-verification hedges first. "Cut description before you cut doubt."
- New contract rule: size the reply to the question, not the work (~150 words
  for a quick status, 250 ceiling).
- Validation round: 21/22 assertions (independent grader), proportionality and
  caveat-retention regressions fixed. Known open defect: one unsourced effort
  estimate survived — tracked for 0.4.

## 0.2.0 — 2026-08-06

- Folded in external prior art: ASD-STE100 sentence architecture (one idea per
  sentence, keep articles and verbs, one name per thing, warnings first),
  caveman's deletion targets and never-drop-negations rule, meat's altitude
  filter (report what the reader must judge).
- Independent review verdict on this version: don't ship — outputs grew ~8%,
  caveats got cut, 4 of 6 tested outputs contained unsupported claims. Led to 0.3.0.

## 0.1.0 — 2026-08-06

- Initial skill: verdict-first contract, one-pass readability rules, selection
  over compression, structure-mirrors-logic, calibrated claims, 12 named
  anti-patterns, the grok test, three modes (write/review/rewrite).
- First A/B round on Opus subagents: 19/19 with skill vs 15/19 baseline; every
  baseline failure structural (arrow chains, headers on chat replies, trailing
  recap).
