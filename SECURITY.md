# Security

This repo ships a prompt-only skill (`SKILL.md`): it runs no code and handles no
credentials. The supporting Python scripts import only the standard library.
`scripts/lint_output.py` reads text and reports findings. `scripts/eval_harness.py`
validates, generates and grades eval suites, and writes results to local files.
Two of its modes run external, third-party model CLIs that you install and
authenticate yourself: `run` calls `claude`, and `grade` calls `hermes`. This repo
does not vendor or pin either, so their supply chain is yours to review. CI runs
only the `validate` mode, which calls neither.

The `jsonwebtoken` strings in `evals/runs/` are the npm package name quoted in
verbatim model output, kept as evidence. They are not credentials.

## Supported versions

Only the latest release on `main` receives fixes.

## Reporting a vulnerability

Report privately. Don't put vulnerability details in a public issue, pull request
or discussion.

1. If this repo's **Security** tab shows a **Report a vulnerability** button, use it.
   That is GitHub's private vulnerability reporting.
2. If the button isn't there, open a public issue titled "Security contact
   request" with no details. I'll reply there to set up a private channel.

I aim to respond within a week. Credit goes to the reporter in the fix notes
unless you prefer otherwise.
