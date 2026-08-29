from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "eval_harness", ROOT / "scripts" / "eval_harness.py"
)
assert SPEC and SPEC.loader
eval_harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(eval_harness)


class EvalHarnessTests(unittest.TestCase):
    def summary_args(self, runs: Path) -> argparse.Namespace:
        return argparse.Namespace(
            suite=ROOT / "evals" / "v2" / "evals.json",
            runs=runs,
            skill=ROOT / "SKILL.md",
            trials=3,
            output=None,
            require_adjudication=True,
        )

    def test_public_v2_suite_is_valid(self) -> None:
        suite = eval_harness.validate_suite(ROOT / "evals" / "v2" / "evals.json")
        self.assertEqual("grokkable-output-v2", suite["suite_id"])
        self.assertEqual(4, len(suite["scenarios"]))
        self.assertEqual(
            {"write", "review_rewrite"},
            {scenario["mode"] for scenario in suite["scenarios"]},
        )

    def test_duplicate_expectation_id_fails_closed(self) -> None:
        source = json.loads((ROOT / "evals" / "v2" / "evals.json").read_text())
        source["scenarios"][0]["expectations"].append(
            dict(source["scenarios"][0]["expectations"][0])
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "fixture.md"
            fixture.write_text("fixture", encoding="utf-8")
            for scenario in source["scenarios"]:
                scenario["fixture"] = "fixture.md"
            suite = root / "evals.json"
            suite.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(eval_harness.HarnessError, "repeats"):
                eval_harness.validate_suite(suite)

    def test_prompts_isolate_skill_and_baseline_conditions(self) -> None:
        suite_path = ROOT / "evals" / "v2" / "evals.json"
        scenario = eval_harness.validate_suite(suite_path)["scenarios"][0]
        skill = "UNIQUE SKILL CONTENT"
        with_skill = eval_harness.generation_prompt(
            suite_path, scenario, "with_skill", skill
        )
        baseline = eval_harness.generation_prompt(
            suite_path, scenario, "without_skill", skill
        )
        self.assertIn(skill, with_skill)
        self.assertNotIn(skill, baseline)
        self.assertIn("baseline condition", baseline)

    def test_claude_output_requires_nonempty_result(self) -> None:
        with self.assertRaises(eval_harness.HarnessError):
            eval_harness.parse_claude_output('{"result":""}')
        reply, payload = eval_harness.parse_claude_output(
            '{"result":"A result","is_error":false}'
        )
        self.assertEqual("A result\n", reply)
        self.assertFalse(payload["is_error"])

    def test_grader_json_extraction_ignores_session_prefix(self) -> None:
        value = eval_harness.extract_json_object(
            'session_id: abc\n{"expectations": []}\n'
        )
        self.assertEqual([], value["expectations"])

    def test_hermes_session_pattern_accepts_stderr_shape(self) -> None:
        stream = '{"expectations": []}\n\nsession_id: 20260828_123456_abcdef\n'
        match = eval_harness.re.search(r"session_id:\s*(\S+)", stream)
        self.assertIsNotNone(match)
        self.assertEqual("20260828_123456_abcdef", match.group(1))

    def test_grader_must_return_exact_expectation_order(self) -> None:
        suite = eval_harness.validate_suite(ROOT / "evals" / "v2" / "evals.json")
        scenario = suite["scenarios"][0]
        reversed_items = [
            {"id": item["id"], "passed": True, "evidence": "evidence"}
            for item in reversed(scenario["expectations"])
        ]
        with self.assertRaisesRegex(eval_harness.HarnessError, "ids differ"):
            eval_harness.validate_grading(
                {"expectations": reversed_items}, scenario
            )

    def test_public_summary_is_complete_and_applies_verified_overrides(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            eval_harness.summarize_cells(
                self.summary_args(ROOT / "evals" / "runs" / "validation-v2-sonnet5")
            )
        summary = json.loads(output.getvalue())
        self.assertTrue(summary["complete"])
        self.assertEqual(11, summary["adjudication_corrections"])
        self.assertEqual(1, summary["primary_verification_corrections"])
        nonexpert = next(
            cell
            for cell in summary["cells"]
            if cell["scenario"] == "nonexpert-audit"
            and cell["config"] == "with_skill"
        )
        self.assertAlmostEqual(29 / 30, nonexpert["mean_pass_rate"])

    def test_summary_rejects_mutated_word_count(self) -> None:
        source = ROOT / "evals" / "runs" / "validation-v2-sonnet5"
        with tempfile.TemporaryDirectory() as directory:
            runs = Path(directory) / "runs"
            shutil.copytree(source, runs)
            grading_path = (
                runs / "debug-report" / "with_skill" / "trial-1" / "grading.json"
            )
            grading = json.loads(grading_path.read_text(encoding="utf-8"))
            grading["execution_metrics"]["output_words"] += 1
            grading_path.write_text(json.dumps(grading), encoding="utf-8")
            with self.assertRaisesRegex(eval_harness.HarnessError, "word count"):
                with contextlib.redirect_stdout(io.StringIO()):
                    eval_harness.summarize_cells(self.summary_args(runs))


if __name__ == "__main__":
    unittest.main()
