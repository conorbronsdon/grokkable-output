# Eval corpus — provenance

The working artifacts behind the numbers in the main README's Testing section:
fixture input notes (`fixtures/`), assertion sets (`evals.json`), per-iteration
model replies with per-assertion grading (`runs/`), the independent review that
rejected v0.2.0 (`independent-review-v0.2.md`), and the analyst summary
(`RESULTS.md`).

Ground rules for reading it:

- **Everything under `runs/` is verbatim output** — model replies and grader
  JSON as produced, including the graded outputs of v0.4.0 and v0.5.0, which
  failed validation and never shipped. Nothing was edited to read better.
  A consequence: some grader notes reference development-repo working files
  that don't ship here — `analyst-notes.md`, a grader "field spec", and
  `qualitative-review.md` (that one was renamed and ships as
  `independent-review-v0.2.md`).
- **Harness artifacts ship as-is, defects included.** Both `benchmark.md`
  files carry an unfilled `<model-name>` placeholder. Their headers say
  "3 runs each per configuration" and report ± spreads, while only one graded
  reply per cell is archived and `RESULTS.md` lists "n=1 per cell" as suite
  debt — that discrepancy is preserved, not reconciled. Iteration-3's table
  has an all-zero Config B column (no baseline was re-run that round) and a
  token count on a different scale from iteration-1's.
- **`RESULTS.md` is the summary** and the only file edited for publication:
  one sentence that pointed at a private development branch was reworded.
  The replies were produced by Opus-class subagents; iterations 2 onward were
  graded by model instances independent of the skill author.
