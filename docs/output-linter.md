# Output linter prototype

`scripts/lint_output.py` is the bounded v0.6 experiment suggested by the five
prompt-only eval rounds: detect mechanical anti-patterns after writing instead
of adding more prose rules to `SKILL.md`.

It currently flags:

- multi-step arrow chains;
- dense heading/pseudo-heading structure on chat-length replies;
- paragraphs over 100 words or five sentences;
- generic offers of “the full breakdown” that may displace a real decision;
- time estimates for source review; and
- recap headings near the end of an answer.

The distinction between findings matters. `error` is reserved for a clear
contract violation such as an arrow chain. `warning` means the structure needs
human review. `review` means the linter can find a risky claim but cannot decide
whether it is supported; effort estimates are the current example.

Run it on a file or stdin:

```bash
python scripts/lint_output.py reply.md
python scripts/lint_output.py --json reply.md
python scripts/lint_output.py --fail-on warning reply.md
```

The CLI reads and writes UTF-8 explicitly, including redirected stdin/stdout on
Windows. Passing a file path avoids differences between PowerShell versions'
native-pipeline encodings. Markdown code spans, fenced and indented code, HTML
`code`/`pre` blocks, and link destinations are excluded from prose findings.
Already-structured heading, blockquote, and table blocks are not treated as
oversized prose paragraphs. List items are measured individually, so a normal
list stays clean while a single oversized item remains reviewable. Observed
durations are kept distinct from prospective effort estimates at clause
boundaries.

Run the tests:

```bash
python -m unittest discover -s tests -v
```

This prototype does not change or bump the shipped skill. Retrospective matches
against the published corpus can establish detection coverage, not whether the
linter improves future model output. A ship decision still requires fresh runs
and fidelity grading; use at least three runs per scenario before attributing a
change to the lint pass.
