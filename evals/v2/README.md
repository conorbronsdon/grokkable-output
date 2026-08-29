# Evaluation suite v2

This suite fixes four limitations in the historical iteration-1 through
iteration-5 corpus without rewriting those artifacts:

- every scenario has a deterministic word ceiling;
- numeric, mechanism, arithmetic, and open-question fidelity are independently
  graded instead of bundled into one assertion;
- every configuration requires at least three fresh trials;
- a fourth scenario exercises both `review` and `rewrite` modes.

The checked-in validation run used `claude-sonnet-5` for 24 independent reply
generations (four scenarios × two configurations × three trials),
`thinkingmachines/inkling:free` through Hermes for independent grading, and
fresh `claude-sonnet-5` sessions to adjudicate demonstrable grader errors. A
primary verifier applied one additional correction where the repository's
deterministic linter and the reply text directly proved a missed trailing recap.
All 11 Claude corrections changed baseline passes to failures; the primary
correction changed one skilled pass to a failure. Raw Hermes semantic scores
were 108/108 with the skill and 101/108 without it, compared with adjusted
scores of 107/108 and 90/108. This asymmetry is part of the result, not hidden
by the summary.

The exact v0.3.1 skill used for those generations is archived at
`evals/runs/validation-v2-sonnet5/skill.md`. Re-summarization reads that snapshot
rather than the repository's current `SKILL.md`, so a later release cannot make
the archived prompt hashes fail or silently reinterpret the old run.

## v0.6.0 candidate repair runs

The first focused repair cycle is rejected and non-evidentiary: it changed a
five-minute interval to four minutes, and its exact experimental skill text was
not archived. The run directory says so explicitly rather than substituting a
later skill whose hash does not match.

Focused cycle 2 and the four-scenario regression each archive the exact skill
text used for generation as `skill.md`; both snapshots match the
`skill_sha256` in their generation metadata. Cycle 2 reused cycle 1's unchanged
baseline cells byte-for-byte. That saved an unnecessary regeneration, but it is
not a fresh baseline and is not presented as one; cycle 2 is candidate-repair
evidence, not the final release comparison.

`review-rewrite-v060-final.json` closes the methodology gap exposed in review:
it adds an explicit assertion for the advertised one-line, category-only cut
ledger. The final run requires three fresh skilled and three fresh baseline
generations. Do not copy baseline cells into it.

The final run at `validation-v2-review-rewrite-v060-final` used six fresh
`claude-sonnet-5` generations and archived the exact skill text. After free
Inkling grading, `claude-sonnet-5` adjudication, and three direct-text primary
corrections, skilled outputs passed 11/12 assertions in every trial and ranged
from 393–431 words. Baseline outputs averaged 10.33/12 assertions and ranged
from 443–541 words. All skilled factual and fidelity assertions passed, but the
one-line cut-ledger assertion failed 3/3: the replies used multi-line bullets
and sometimes repeated quotes or rationale. The proportionality repair worked;
the stricter cut-ledger behavior did not. The candidate therefore stops after
three repair cycles without a release claim.

Run from the repository root:

```bash
python scripts/eval_harness.py validate --suite evals/v2/evals.json
python scripts/eval_harness.py run \
  --suite evals/v2/evals.json \
  --skill SKILL.md \
  --output evals/runs/validation-v2-sonnet5 \
  --trials 3 \
  --model sonnet
python scripts/eval_harness.py grade \
  --suite evals/v2/evals.json \
  --runs evals/runs/validation-v2-sonnet5 \
  --trials 3 \
  --model thinkingmachines/inkling:free
python scripts/eval_harness.py adjudicate \
  --suite evals/v2/evals.json \
  --runs evals/runs/validation-v2-sonnet5 \
  --trials 3 \
  --model sonnet
python scripts/eval_harness.py summarize \
  --suite evals/v2/evals.json \
  --runs evals/runs/validation-v2-sonnet5 \
  --trials 3 \
  --require-adjudication \
  --output evals/runs/validation-v2-sonnet5/summary.json
```

The harness is resumable and fails closed on partial cells, malformed provider
JSON, missing or reordered expectation IDs, unverified adjudication overrides,
and incomplete trial counts. Provider credentials remain in their CLIs; no key
or token is written to the corpus.

`--overwrite` is stage-local. After regenerating replies, rerun grading and
adjudication with `--overwrite`; otherwise summarization rejects the stale prompt
hashes rather than silently combining old grades with new replies. Provider
timeouts abort the current command so an ambiguous response is not retried as a
valid cell.

The run measures variance for one generator and two reviewing roles. It does
not establish cross-model generality. Inkling's free endpoint logs prompts and
outputs for model improvement; every fixture and reply in this run is public
repository data.
