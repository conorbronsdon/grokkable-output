"""Supply-chain hygiene: workflow actions pinned to full commit SHAs."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
USES = re.compile(r"""^\s*(?:-\s+)?uses:\s*["']?([^\s"'#]+)""")
FULL_SHA = re.compile(r"@[0-9a-f]{40}$")


def action_refs(yaml_text: str) -> list[str]:
    """Every remote action ref in a workflow (local ./ and docker:// skipped)."""
    refs = []
    for line in yaml_text.splitlines():
        match = USES.match(line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./") or ref.startswith("docker://"):
            continue
        refs.append(ref)
    return refs


def unpinned_uses(yaml_text: str) -> list[str]:
    return [ref for ref in action_refs(yaml_text) if not FULL_SHA.search(ref)]


class UnpinnedUsesTests(unittest.TestCase):
    def test_tag_pin_fires(self) -> None:
        self.assertEqual(
            unpinned_uses("      - uses: actions/checkout@v6\n"), ["actions/checkout@v6"]
        )

    def test_short_sha_and_branch_fire(self) -> None:
        self.assertEqual(
            unpinned_uses("- uses: actions/checkout@d23441a\n  - uses: foo/bar@main\n"),
            ["actions/checkout@d23441a", "foo/bar@main"],
        )

    def test_full_sha_with_comment_and_local_action_do_not_fire(self) -> None:
        text = (
            "      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0\n"
            "      - uses: ./.github/actions/local\n"
        )
        self.assertEqual(unpinned_uses(text), [])


class RepoWorkflowTests(unittest.TestCase):
    def test_workflow_set_is_the_one_covered(self) -> None:
        self.assertEqual(sorted(p.name for p in WORKFLOWS.glob("*.y*ml")), ["ci.yml"])

    def test_every_workflow_action_is_sha_pinned(self) -> None:
        # Name every action ref so a matcher that stops matching fails here
        # instead of passing with nothing checked.
        text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        self.assertEqual(
            [ref.split("@")[0] for ref in action_refs(text)],
            ["actions/checkout", "actions/setup-python"],
        )
        self.assertEqual(unpinned_uses(text), [])

    def test_uses_line_count_matches_parsed_refs(self) -> None:
        for path in WORKFLOWS.glob("*.y*ml"):
            text = path.read_text(encoding="utf-8")
            raw = [l for l in text.splitlines() if re.search(r"\buses\s*:", l)]
            with self.subTest(workflow=path.name):
                self.assertEqual(len(action_refs(text)), len(raw))

    def test_dependabot_watches_github_actions(self) -> None:
        text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertRegex(text, re.compile(r"^\s*- package-ecosystem: github-actions$", re.M))

    def test_security_policy_names_a_private_channel(self) -> None:
        text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("**Report a vulnerability**", text)
        # A fallback that works while private reporting is off, and that
        # still keeps details out of public view.
        flat = " ".join(text.split())
        self.assertIn('"Security contact request" with no details', flat)
        self.assertIn("Don't put vulnerability details in a public issue", flat)


if __name__ == "__main__":
    unittest.main()
