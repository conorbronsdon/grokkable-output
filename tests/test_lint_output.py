import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "lint_output.py"
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
        self.assertNotIn("effort-estimate", self.rules("Stable across 30 minutes of monitoring."))

    def test_large_mechanism_block_fires(self) -> None:
        paragraph = " ".join(["The retry increased latency."] * 26)
        self.assertIn("oversized-block", self.rules(paragraph))

    def test_short_plain_reply_is_clean(self) -> None:
        text = "The rollback fixed the 500s. The sandbox endpoint caused rate limits, retries, and timeouts."
        self.assertEqual([], LINTER.lint(text))

    def test_trailing_recap_fires_only_near_end(self) -> None:
        text = ("The fix is deployed. " * 20) + "\n\nBottom line: monitoring is stable."
        self.assertIn("trailing-recap", self.rules(text))


if __name__ == "__main__":
    unittest.main()
