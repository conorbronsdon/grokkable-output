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

The run measures variance for one generator and two reviewing roles. It does
not establish cross-model generality. Inkling's free endpoint logs prompts and
outputs for model improvement; every fixture and reply in this run is public
repository data.
