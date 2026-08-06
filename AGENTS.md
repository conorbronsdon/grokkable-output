# Agent instructions — grokkable-output

This repo ships one artifact: `SKILL.md`, a portable agent skill that changes how
an agent writes replies, reports, and status updates (verdict first, one-pass
readable, calibrated claims). Everything else supports it.

## Layout

- `SKILL.md` — the skill. The only file consumers need.
- `examples/` — real, unedited before/after pairs from A/B testing on Opus
  subagents. Generated artifacts: regenerate only by re-running the eval harness
  in the development repo, never by hand-editing (they are evidence, not prose).
- `README.md` — positioning, install, testing summary, related work.

## Rules for working in this repo

- **Apply the skill to your own output here.** A PR description or issue reply in
  this repo that buries its lede is a bug report against the product. Unenforced —
  no hook checks this; reviewers do.
- **Examples are evidence.** Never edit files under `examples/` to read better.
  Their value is that they are verbatim model output. Unenforced by tooling;
  provenance is documented in `examples/README.md`.
- **Testing claims in README.md must trace to the eval corpus.** Scores (21/22,
  15/19, word counts) come from the development repo's graded runs. If you change
  a claim, cite the grading it comes from. Unenforced — no CI yet; treat any
  unsourced number as a defect (the skill's own rule).
- **Keep the SKILL.md frontmatter complete** (name, description, version, license,
  compatibility, metadata) — agentskills.io and marketplace listers read it.
- Version bumps follow semver on skill content: pattern/rule changes are minor,
  wording fixes are patch.
