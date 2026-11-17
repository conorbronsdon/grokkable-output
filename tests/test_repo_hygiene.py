"""Supply-chain hygiene: workflow actions pinned to full commit SHAs."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
USES = re.compile(r"""^\s*(?:-\s+)?uses:\s*["']?([^\s"'#]+)""")
FULL_SHA = re.compile(r"@[0-9a-f]{40}$")


def unpinned_uses(yaml_text: str) -> list[str]:
    bad = []
    for line in yaml_text.splitlines():
        match = USES.match(line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./") or ref.startswith("docker://"):
            continue
        if not FULL_SHA.search(ref):
            bad.append(ref)
    return bad


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
        for path in WORKFLOWS.glob("*.y*ml"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(workflow=path.name):
                self.assertIn("uses:", text)
                self.assertEqual(unpinned_uses(text), [])

    def test_dependabot_watches_github_actions(self) -> None:
        text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertRegex(text, re.compile(r"^\s*- package-ecosystem: github-actions$", re.M))

    def test_security_policy_names_a_private_channel(self) -> None:
        text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("Report a vulnerability", text)


if __name__ == "__main__":
    unittest.main()
