import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scripts" / "lint_output.py"
SPEC = importlib.util.spec_from_file_location("lint_output", MODULE_PATH)
assert SPEC and SPEC.loader
LINTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LINTER
SPEC.loader.exec_module(LINTER)


class LintOutputTests(unittest.TestCase):
    def rules(self, text: str) -> set[str]:
        return {finding.rule for finding in LINTER.lint(text)}

    def test_known_positive_arrow_chain_fires(self) -> None:
        self.assertIn("arrow-chain", self.rules("host → 429s → retries → timeout → 500"))

    def test_known_negative_single_arrow_does_not_fire(self) -> None:
        self.assertNotIn("arrow-chain", self.rules("Before → after."))

    def test_compact_arrow_chain_fires(self) -> None:
        findings = [
            item for item in LINTER.lint("host->429s->timeout->500")
            if item.rule == "arrow-chain"
        ]
        self.assertEqual(1, len(findings))

    def test_v05_depth_offer_fires(self) -> None:
        self.assertIn("depth-offer", self.rules("Want the full breakdown?"))

    def test_concrete_decision_does_not_fire_as_depth_offer(self) -> None:
        text = "Do you want me to open the production API-key request today?"
        self.assertNotIn("depth-offer", self.rules(text))

    def test_unsourced_estimate_is_review_not_proven_error(self) -> None:
        findings = LINTER.lint("Setting one up is about an hour.")
        estimate = next(item for item in findings if item.rule == "effort-estimate")
        self.assertEqual("review", estimate.severity)

    def test_observed_duration_is_not_assumed_to_be_estimate(self) -> None:
        for text in (
            "Stable across 30 minutes of monitoring.",
            "Error rates stayed flat over 30 minutes of monitoring.",
        ):
            with self.subTest(text=text):
                self.assertNotIn("effort-estimate", self.rules(text))

    def test_large_mechanism_block_fires(self) -> None:
        paragraph = " ".join(["The retry increased latency."] * 26)
        self.assertIn("oversized-block", self.rules(paragraph))

    def test_later_oversized_block_reports_content_line(self) -> None:
        text = "First.\n\n" + "Sentence. " * 6
        finding = next(item for item in LINTER.lint(text) if item.rule == "oversized-block")
        self.assertEqual(3, finding.line)

    def test_paragraph_leading_pseudo_headings_count_toward_density(self) -> None:
        text = "\n\n".join(
            [
                "**Decision.** Use the existing API.",
                "**Evidence.** The compatibility test passed.",
                "**Next step.** Deploy the bounded change.",
            ]
        )
        self.assertIn("heading-density", self.rules(text))

    def test_published_pseudo_heading_failure_is_detected(self) -> None:
        corpus_reply = ROOT / "evals" / "runs" / "iteration-1" / "eval-1-migration-status" / "without_skill" / "reply.md"
        self.assertIn(
            "heading-density",
            self.rules(corpus_reply.read_text(encoding="utf-8")),
        )

    def test_short_plain_reply_is_clean(self) -> None:
        text = "The rollback fixed the 500s. The sandbox endpoint caused rate limits, retries, and timeouts."
        self.assertEqual([], LINTER.lint(text))

    def test_trailing_recap_fires_only_near_end(self) -> None:
        text = ("The fix is deployed. " * 20) + "\n\nBottom line: monitoring is stable."
        self.assertIn("trailing-recap", self.rules(text))

    def test_cli_forces_utf8_for_file_stdin_plain_and_json(self) -> None:
        text = "host → 429s → timeout\n"
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "cp1252"
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "reply.md"
            path.write_text(text, encoding="utf-8")
            plain = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--fail-on", "never", str(path)],
                check=False,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(0, plain.returncode, plain.stderr.decode(errors="replace"))
            self.assertIn("→".encode(), plain.stdout)

            structured = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--json"],
                input=text.encode(),
                check=False,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(1, structured.returncode)
            self.assertEqual(b"", structured.stderr)
            payload = json.loads(structured.stdout.decode("utf-8"))
            self.assertEqual("arrow-chain", payload[0]["rule"])


if __name__ == "__main__":
    unittest.main()
