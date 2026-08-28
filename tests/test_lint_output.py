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

    def test_independent_arrow_mappings_do_not_form_a_chain(self) -> None:
        text = "Before → after. Source → destination."
        self.assertNotIn("arrow-chain", self.rules(text))

    def test_compact_arrow_chain_fires(self) -> None:
        findings = [
            item for item in LINTER.lint("host->429s->timeout->500")
            if item.rule == "arrow-chain"
        ]
        self.assertEqual(1, len(findings))

    def test_arrow_chain_in_fenced_code_does_not_fire(self) -> None:
        text = "Example:\n\n```python\ndef f(x: A) -> B -> C:\n    return x\n```\n"
        self.assertNotIn("arrow-chain", self.rules(text))

    def test_arrow_chain_in_nonprose_markdown_does_not_fire(self) -> None:
        cases = (
            "Use `A -> B -> C` as the signature.",
            "Use ``A ` literal -> B -> C`` as the signature.",
            "See [flow](https://x.test/a->b->c).",
            "See [flow](https://x.test/a_(b)->c->d).",
            "See <https://x.test/a->b->c>.",
            "[flow]: https://x.test/a->b->c",
            "Example:\n\n    def f(x: A) -> B -> C\n",
            "> ```text\n> A -> B -> C\n> ```",
            "<pre>A -> B -> C</pre>",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertNotIn("arrow-chain", self.rules(text))

    def test_unclosed_fence_masks_code_to_end_but_not_prior_prose(self) -> None:
        text = "The host -> retries -> timeout.\n\n```text\ncode -> value -> value"
        findings = [item for item in LINTER.lint(text) if item.rule == "arrow-chain"]
        self.assertEqual(1, len(findings))
        self.assertEqual(1, findings[0].line)

    def test_unclosed_blockquote_fence_ends_with_container(self) -> None:
        text = "> ```text\n> code -> value -> value\nOutside host -> retries -> timeout."
        findings = [item for item in LINTER.lint(text) if item.rule == "arrow-chain"]
        self.assertEqual(1, len(findings))
        self.assertEqual(3, findings[0].line)

    def test_prose_around_nonprose_markdown_still_fires(self) -> None:
        text = "Use `A -> B -> C` as an example. The host -> retries -> timeout."
        findings = [item for item in LINTER.lint(text) if item.rule == "arrow-chain"]
        self.assertEqual(1, len(findings))
        self.assertEqual("-> retries ->", findings[0].excerpt)

    def test_escaped_or_masked_ticks_do_not_hide_later_prose(self) -> None:
        cases = (
            "A literal \\` marker. The host -> retries -> timeout. Then `ok`.",
            "```text\none ` marker\n```\nThe host -> retries -> timeout. Then `ok`.",
            "<code>one ` marker</code> The host -> retries -> timeout. Then `ok`.",
            "An unmatched ` marker.\n\nThe host -> retries -> timeout. Then `ok`.",
        )
        for text in cases:
            with self.subTest(text=text):
                findings = [item for item in LINTER.lint(text) if item.rule == "arrow-chain"]
                self.assertEqual(1, len(findings))

    def test_malformed_link_destination_does_not_hide_prose(self) -> None:
        text = "See [broken](https://x.test/a_(b Outside host -> retries -> timeout.))"
        self.assertIn("arrow-chain", self.rules(text))

    def test_independent_same_line_mappings_do_not_form_a_chain(self) -> None:
        for text in (
            "Before -> after; source -> destination.",
            "| Before -> after | Source -> destination |",
            "A -> B, while C -> D.",
        ):
            with self.subTest(text=text):
                self.assertNotIn("arrow-chain", self.rules(text))

    def test_semicolon_causal_chain_with_shared_bridge_fires(self) -> None:
        for text in (
            "host -> 429; 429 -> retries",
            "cache miss -> database query; query delay -> timeout",
        ):
            with self.subTest(text=text):
                self.assertIn("arrow-chain", self.rules(text))

    def test_v05_depth_offer_fires(self) -> None:
        self.assertIn("depth-offer", self.rules("Want the full breakdown?"))

    def test_concrete_decision_does_not_fire_as_depth_offer(self) -> None:
        text = "Do you want me to open the production API-key request today?"
        self.assertNotIn("depth-offer", self.rules(text))

    def test_unsourced_estimate_is_review_not_proven_error(self) -> None:
        findings = LINTER.lint("Setting one up is about an hour.")
        estimate = next(item for item in findings if item.rule == "effort-estimate")
        self.assertEqual("review", estimate.severity)

    def test_contextual_over_estimate_fires(self) -> None:
        self.assertIn(
            "effort-estimate",
            self.rules("The migration will take over two weeks."),
        )

    def test_observed_duration_is_not_assumed_to_be_estimate(self) -> None:
        for text in (
            "Stable across 30 minutes of monitoring.",
            "Error rates stayed flat over 30 minutes of monitoring.",
            "The migration completed in about an hour.",
            "Backups are retained for up to 30 days.",
            "Latency stayed flat across 30-60 minutes of monitoring.",
            "Supported for 7-14 days after signup.",
        ):
            with self.subTest(text=text):
                self.assertNotIn("effort-estimate", self.rules(text))

    def test_prospective_estimate_with_observation_word_still_fires(self) -> None:
        cases = (
            "The supported migration will take roughly two days.",
            "Planning completed; migration will take about two days.",
            "The dry run took one hour; production will take about two days.",
            "The dry run took one hour and production will take about two days.",
            "Planning completed and migration is expected to take about two days.",
            "Planning completed and migration takes about two days.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertIn("effort-estimate", self.rules(text))

    def test_large_mechanism_block_fires(self) -> None:
        paragraph = " ".join(["The retry increased latency."] * 26)
        self.assertIn("oversized-block", self.rules(paragraph))

    def test_existing_markdown_structure_is_not_an_oversized_paragraph(self) -> None:
        cases = (
            "\n".join(f"- Item {index}." for index in range(6)),
            "\n".join(f"{index}. Step {index}." for index in range(1, 7)),
            "\n".join(f"# Heading {index}" for index in range(1, 7)),
            "| A | B |\n|---|---|\n" + "\n".join(f"| {index}. | value. |" for index in range(6)),
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertNotIn("oversized-block", self.rules(text))

    def test_oversized_list_item_still_fires(self) -> None:
        text = "- " + "Sentence with enough words to be prose. " * 16
        self.assertIn("oversized-block", self.rules(text))

    def test_oversized_nested_list_item_still_fires(self) -> None:
        text = "- Parent.\n    - " + "Sentence with enough words to be prose. " * 16
        findings = [item for item in LINTER.lint(text) if item.rule == "oversized-block"]
        self.assertEqual(1, len(findings))
        self.assertEqual(2, findings[0].line)

    def test_top_level_indented_bullet_code_does_not_fire(self) -> None:
        text = "    - A -> B -> C"
        self.assertNotIn("arrow-chain", self.rules(text))

    def test_top_level_indented_numbered_code_does_not_fire(self) -> None:
        text = "    1. A -> B -> C"
        self.assertNotIn("arrow-chain", self.rules(text))

    def test_blockquoted_indented_code_does_not_fire(self) -> None:
        text = ">     def f(x: A) -> B -> C"
        self.assertNotIn("arrow-chain", self.rules(text))

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
        finding = next(item for item in LINTER.lint(text) if item.rule == "heading-density")
        self.assertEqual(5, finding.line)

    def test_heading_density_cutoff_and_early_recap_do_not_fire(self) -> None:
        long_text = "# One\n\n# Two\n\n# Three\n\n" + "word " * 501
        self.assertNotIn("heading-density", self.rules(long_text))

        early_recap = "Summary: the fix worked.\n\n" + "Evidence sentence. " * 30
        self.assertNotIn("trailing-recap", self.rules(early_recap))

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

    def test_cli_fail_on_thresholds_are_ordered(self) -> None:
        cases = {
            "review": "Setting one up is about an hour.",
            "warning": "Want the full breakdown?",
            "error": "host -> retries -> timeout",
        }
        expected = {
            "never": {"review": 0, "warning": 0, "error": 0},
            "error": {"review": 0, "warning": 0, "error": 1},
            "warning": {"review": 0, "warning": 1, "error": 1},
            "review": {"review": 1, "warning": 1, "error": 1},
        }
        for threshold, outcomes in expected.items():
            for finding_type, returncode in outcomes.items():
                with self.subTest(threshold=threshold, finding_type=finding_type):
                    result = subprocess.run(
                        [sys.executable, str(MODULE_PATH), "--fail-on", threshold],
                        input=cases[finding_type],
                        text=True,
                        encoding="utf-8",
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                    )
                    self.assertEqual(returncode, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
