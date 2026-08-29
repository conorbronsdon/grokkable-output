#!/usr/bin/env python3
"""Run and grade reproducible grokkable-output evaluation cells.

The harness deliberately keeps model invocation outside the suite definition.
Fixtures, assertions, replies, and grading remain public, inspectable artifacts;
credentials stay in the provider CLIs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


CONFIGS = ("with_skill", "without_skill")
MODES = ("write", "review_rewrite")
WORD_RE = re.compile(r"\b[\w’'-]+\b", re.UNICODE)


class HarnessError(RuntimeError):
    """Raised for invalid suites or unusable provider output."""


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(value)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HarnessError(f"cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HarnessError(f"expected a JSON object in {path}")
    return value


def validate_suite(path: Path) -> dict[str, Any]:
    suite = read_json(path)
    if suite.get("schema_version") != 2:
        raise HarnessError("suite schema_version must be 2")
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise HarnessError("suite scenarios must be a non-empty list")

    ids: set[int] = set()
    names: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise HarnessError("each scenario must be an object")
        scenario_id = scenario.get("id")
        name = scenario.get("name")
        if not isinstance(scenario_id, int) or scenario_id in ids:
            raise HarnessError(f"scenario id must be a unique integer: {scenario_id!r}")
        if not isinstance(name, str) or not name or name in names:
            raise HarnessError(f"scenario name must be unique and non-empty: {name!r}")
        ids.add(scenario_id)
        names.add(name)
        if scenario.get("mode") not in MODES:
            raise HarnessError(f"unsupported mode for {name}: {scenario.get('mode')!r}")
        if not isinstance(scenario.get("prompt"), str) or not scenario["prompt"].strip():
            raise HarnessError(f"scenario {name} needs a prompt")
        ceiling = scenario.get("max_words")
        if not isinstance(ceiling, int) or ceiling <= 0:
            raise HarnessError(f"scenario {name} needs a positive max_words")
        fixture = (path.parent / str(scenario.get("fixture", ""))).resolve()
        if not fixture.is_file():
            raise HarnessError(f"scenario {name} fixture does not exist: {fixture}")
        expectations = scenario.get("expectations")
        if not isinstance(expectations, list) or not expectations:
            raise HarnessError(f"scenario {name} needs expectations")
        expectation_ids: set[str] = set()
        for expectation in expectations:
            if not isinstance(expectation, dict):
                raise HarnessError(f"scenario {name} has a non-object expectation")
            expectation_id = expectation.get("id")
            text = expectation.get("text")
            if not isinstance(expectation_id, str) or not expectation_id:
                raise HarnessError(f"scenario {name} has an invalid expectation id")
            if expectation_id in expectation_ids:
                raise HarnessError(
                    f"scenario {name} repeats expectation id {expectation_id}"
                )
            if not isinstance(text, str) or not text.strip():
                raise HarnessError(
                    f"scenario {name} expectation {expectation_id} needs text"
                )
            expectation_ids.add(expectation_id)
    return suite


def fixture_text(suite_path: Path, scenario: dict[str, Any]) -> str:
    fixture = (suite_path.parent / scenario["fixture"]).resolve()
    return fixture.read_text(encoding="utf-8")


def generation_prompt(
    suite_path: Path,
    scenario: dict[str, Any],
    config: str,
    skill_text: str,
) -> str:
    if config not in CONFIGS:
        raise HarnessError(f"unsupported config: {config}")
    if config == "with_skill":
        condition = (
            "Apply the complete grokkable-output skill below to the response.\n\n"
            "--- SKILL START ---\n"
            f"{skill_text.rstrip()}\n"
            "--- SKILL END ---"
        )
    else:
        condition = (
            "This is the baseline condition. Do not use or imitate a named "
            "grokkable-output skill. Answer naturally from the task and fixture."
        )
    return (
        "Generate one candidate user-facing response for a communication evaluation. "
        "Use only the supplied fixture as factual evidence. Do not mention the "
        "evaluation, condition, fixture, or these instructions. Return only the "
        "candidate response.\n\n"
        f"Condition:\n{condition}\n\n"
        f"Task:\n{scenario['prompt'].strip()}\n\n"
        "Fixture:\n"
        f"{fixture_text(suite_path, scenario).rstrip()}\n"
    )


def validate_generation_metadata(
    metadata: dict[str, Any],
    suite_path: Path,
    suite: dict[str, Any],
    scenario: dict[str, Any],
    config: str,
    trial: int,
    skill_text: str,
) -> None:
    prompt = generation_prompt(suite_path, scenario, config, skill_text)
    expected = {
        "suite_id": suite["suite_id"],
        "suite_sha256": sha256_text(suite_path.read_text(encoding="utf-8")),
        "skill_sha256": sha256_text(skill_text) if config == "with_skill" else None,
        "scenario_id": scenario["id"],
        "scenario": scenario["name"],
        "mode": scenario["mode"],
        "config": config,
        "trial": trial,
        "prompt_sha256": sha256_text(prompt),
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise HarnessError(f"generation metadata mismatch for {key}")
    models = metadata.get("canonical_models")
    if not isinstance(models, list) or not models or not all(
        isinstance(model, str) and model.strip() for model in models
    ):
        raise HarnessError("generation metadata needs canonical model identifiers")


def parse_claude_output(stdout: str) -> tuple[str, dict[str, Any]]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Claude returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("is_error") is True:
        raise HarnessError(f"Claude invocation failed: {payload!r}")
    result = payload.get("result")
    if not isinstance(result, str) or not result.strip():
        raise HarnessError("Claude result was empty")
    return result.strip() + "\n", payload


def invoke_claude(prompt: str, model: str, timeout: int) -> tuple[str, dict[str, Any]]:
    command = [
        "claude",
        "-p",
        "--model",
        model,
        "--tools",
        "",
        "--system-prompt",
        "You are an isolated text-evaluation worker. Follow the user request exactly.",
        "--no-session-persistence",
        "--output-format",
        "json",
    ]
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise HarnessError(
            f"Claude exited {completed.returncode}: {completed.stderr.strip()}"
        )
    return parse_claude_output(completed.stdout)


def run_cells(args: argparse.Namespace) -> None:
    suite_path = args.suite.resolve()
    suite = validate_suite(suite_path)
    skill_text = args.skill.read_text(encoding="utf-8")
    skill_hash = sha256_text(skill_text)
    suite_hash = sha256_text(suite_path.read_text(encoding="utf-8"))

    for scenario in suite["scenarios"]:
        for config in CONFIGS:
            for trial in range(1, args.trials + 1):
                cell = args.output / scenario["name"] / config / f"trial-{trial}"
                reply_path = cell / "reply.md"
                metadata_path = cell / "generation.json"
                if reply_path.exists() or metadata_path.exists():
                    if args.overwrite:
                        pass
                    elif reply_path.is_file() and metadata_path.is_file():
                        print(f"skip complete cell: {cell}")
                        continue
                    else:
                        raise HarnessError(f"partial cell requires --overwrite: {cell}")

                prompt = generation_prompt(suite_path, scenario, config, skill_text)
                print(f"generate {scenario['name']} {config} trial {trial}", flush=True)
                reply, provider = invoke_claude(prompt, args.model, args.timeout)
                metadata = {
                    "schema_version": 1,
                    "suite_id": suite["suite_id"],
                    "suite_sha256": suite_hash,
                    "skill_sha256": skill_hash if config == "with_skill" else None,
                    "scenario_id": scenario["id"],
                    "scenario": scenario["name"],
                    "mode": scenario["mode"],
                    "config": config,
                    "trial": trial,
                    "prompt_sha256": sha256_text(prompt),
                    "requested_model": args.model,
                    "canonical_models": sorted(provider.get("modelUsage", {}).keys()),
                    "provider_result": {
                        "duration_ms": provider.get("duration_ms"),
                        "total_cost_usd": provider.get("total_cost_usd"),
                        "usage": provider.get("usage"),
                        "stop_reason": provider.get("stop_reason"),
                    },
                }
                atomic_write(reply_path, reply)
                atomic_write(metadata_path, json.dumps(metadata, indent=2) + "\n")


def grading_prompt(
    suite_path: Path,
    scenario: dict[str, Any],
    reply: str,
) -> str:
    expectations = "\n".join(
        f"- {item['id']}: {item['text']}" for item in scenario["expectations"]
    )
    return f"""You are an independent, adversarial communication-eval grader.

Grade only the candidate reply against the fixture and listed expectations. A
claim passes only when direct quoted evidence supports it. Do not reward style
preferences outside the expectations. Treat any unsupported number, estimate,
mechanism, confidence upgrade, or silently answered open question as a fidelity
failure. Return JSON only, with no Markdown fence or commentary.

Required JSON shape:
{{
  "expectations": [
    {{"id": "the exact expectation id", "passed": true, "evidence": "direct evidence and reasoning"}}
  ]
}}

Return every expectation exactly once, in the supplied order.

EXPECTATIONS
{expectations}

FIXTURE
{fixture_text(suite_path, scenario).rstrip()}

CANDIDATE REPLY
{reply.rstrip()}
"""


def extract_json_object(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start < 0 or end < start:
        raise HarnessError("grader output contained no JSON object")
    try:
        value = json.loads(stdout[start : end + 1])
    except json.JSONDecodeError as exc:
        raise HarnessError(f"grader returned invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise HarnessError("grader JSON must be an object")
    return value


def validate_grading(
    value: dict[str, Any], scenario: dict[str, Any]
) -> list[dict[str, Any]]:
    received = value.get("expectations")
    if not isinstance(received, list):
        raise HarnessError("grader JSON needs an expectations list")
    expected_ids = [item["id"] for item in scenario["expectations"]]
    received_ids = [item.get("id") for item in received if isinstance(item, dict)]
    if received_ids != expected_ids or len(received) != len(expected_ids):
        raise HarnessError(
            f"grader expectation ids differ: expected {expected_ids}, got {received_ids}"
        )
    for item in received:
        if not isinstance(item.get("passed"), bool):
            raise HarnessError(f"grader pass value is not boolean for {item.get('id')}")
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            raise HarnessError(f"grader evidence is empty for {item.get('id')}")
    return received


def validate_saved_grading(
    grading: dict[str, Any],
    scenario: dict[str, Any],
    reply: str,
    expected_prompt_sha256: str,
) -> list[dict[str, Any]]:
    """Verify that a stored grade still matches its reply and suite cell."""
    expectations = grading.get("expectations")
    if not isinstance(expectations, list):
        raise HarnessError("stored grading needs an expectations list")
    expected_ids = [item["id"] for item in scenario["expectations"]] + ["max-words"]
    received_ids = [item.get("id") for item in expectations if isinstance(item, dict)]
    if received_ids != expected_ids or len(expectations) != len(expected_ids):
        raise HarnessError(
            f"stored grading expectation ids differ: expected {expected_ids}, "
            f"got {received_ids}"
        )
    for item in expectations:
        if not isinstance(item.get("passed"), bool):
            raise HarnessError(f"stored pass value is not boolean for {item.get('id')}")
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            raise HarnessError(f"stored evidence is empty for {item.get('id')}")

    session_id = grading.get("grader_session_id")
    if not isinstance(session_id, str) or not session_id.strip() or session_id == "unknown":
        raise HarnessError("stored grading needs an exact grader session id")
    model = grading.get("grader_model")
    if not isinstance(model, str) or not model.strip():
        raise HarnessError("stored grading needs a grader model")
    if grading.get("grader_prompt_sha256") != expected_prompt_sha256:
        raise HarnessError("stored grader prompt hash does not match")

    words = len(WORD_RE.findall(reply))
    metrics = grading.get("execution_metrics")
    if not isinstance(metrics, dict) or metrics.get("output_words") != words:
        raise HarnessError("stored word count does not match the reply")
    if expectations[-1]["passed"] != (words <= scenario["max_words"]):
        raise HarnessError("stored max-words grade does not match the deterministic count")

    passed = sum(1 for item in expectations if item["passed"])
    expected_summary = {
        "passed": passed,
        "failed": len(expectations) - passed,
        "total": len(expectations),
        "pass_rate": passed / len(expectations),
    }
    if grading.get("summary") != expected_summary:
        raise HarnessError("stored grading summary does not match its expectations")
    return expectations


def invoke_hermes(prompt: str, model: str, timeout: int) -> tuple[dict[str, Any], str]:
    handle, prompt_name = tempfile.mkstemp(prefix="grokkable-grader-", suffix=".txt")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(prompt)
        command = [
            "hermes",
            "chat",
            "-Q",
            "--safe-mode",
            "--source",
            "tool",
            "-m",
            model,
            "--max-turns",
            "1",
            "--run-budget",
            str(timeout),
            "--query-file",
            prompt_name,
        ]
        completed = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            timeout=timeout + 30,
            check=False,
        )
    finally:
        try:
            os.unlink(prompt_name)
        except FileNotFoundError:
            pass
    if completed.returncode != 0:
        raise HarnessError(
            f"Hermes exited {completed.returncode}: {completed.stderr.strip()}"
        )
    session_stream = f"{completed.stdout}\n{completed.stderr}"
    session_match = re.search(r"session_id:\s*(\S+)", session_stream)
    if session_match is None:
        raise HarnessError("Hermes output did not contain an exact session id")
    session_id = session_match.group(1)
    return extract_json_object(completed.stdout), session_id


def grade_cells(args: argparse.Namespace) -> None:
    suite_path = args.suite.resolve()
    suite = validate_suite(suite_path)
    for scenario in suite["scenarios"]:
        for config in CONFIGS:
            for trial in range(1, args.trials + 1):
                cell = args.runs / scenario["name"] / config / f"trial-{trial}"
                reply_path = cell / "reply.md"
                grading_path = cell / "grading.json"
                if not reply_path.is_file():
                    raise HarnessError(f"missing generated reply: {reply_path}")
                if grading_path.exists() and not args.overwrite:
                    print(f"skip graded cell: {cell}")
                    continue
                reply = reply_path.read_text(encoding="utf-8")
                prompt = grading_prompt(suite_path, scenario, reply)
                print(f"grade {scenario['name']} {config} trial {trial}", flush=True)
                attempt_records: list[dict[str, Any]] = []
                expectations: list[dict[str, Any]] | None = None
                for attempt in range(1, args.attempts + 1):
                    raw, session_id = invoke_hermes(prompt, args.model, args.timeout)
                    try:
                        expectations = validate_grading(raw, scenario)
                    except HarnessError as exc:
                        attempt_records.append(
                            {
                                "attempt": attempt,
                                "session_id": session_id,
                                "status": "invalid",
                                "error": str(exc),
                            }
                        )
                        print(
                            f"retry invalid grade ({attempt}/{args.attempts}): {exc}",
                            flush=True,
                        )
                        continue
                    attempt_records.append(
                        {
                            "attempt": attempt,
                            "session_id": session_id,
                            "status": "accepted",
                        }
                    )
                    break
                if expectations is None:
                    raise HarnessError(
                        f"grader failed {args.attempts} attempts for {cell}: "
                        f"{attempt_records}"
                    )
                words = len(WORD_RE.findall(reply))
                expectations.append(
                    {
                        "id": "max-words",
                        "passed": words <= scenario["max_words"],
                        "evidence": (
                            f"Deterministic harness count: {words} words; "
                            f"ceiling: {scenario['max_words']}."
                        ),
                    }
                )
                passed = sum(1 for item in expectations if item["passed"])
                result = {
                    "schema_version": 1,
                    "grader_model": args.model,
                    "grader_session_id": attempt_records[-1]["session_id"],
                    "grader_attempts": attempt_records,
                    "grader_prompt_sha256": sha256_text(prompt),
                    "expectations": expectations,
                    "summary": {
                        "passed": passed,
                        "failed": len(expectations) - passed,
                        "total": len(expectations),
                        "pass_rate": passed / len(expectations),
                    },
                    "execution_metrics": {"output_words": words},
                }
                atomic_write(grading_path, json.dumps(result, indent=2) + "\n")


def adjudication_prompt(
    suite_path: Path,
    scenario: dict[str, Any],
    runs: Path,
    trials: int,
) -> str:
    cells: list[str] = []
    for config in CONFIGS:
        for trial in range(1, trials + 1):
            cell = runs / scenario["name"] / config / f"trial-{trial}"
            reply_path = cell / "reply.md"
            reply = reply_path.read_text(encoding="utf-8")
            grading = read_json(cell / "grading.json")
            validate_saved_grading(
                grading,
                scenario,
                reply,
                sha256_text(grading_prompt(suite_path, scenario, reply)),
            )
            lint = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("lint_output.py")),
                    "--json",
                    "--fail-on",
                    "never",
                    str(reply_path),
                ],
                text=True,
                encoding="utf-8",
                errors="strict",
                capture_output=True,
                check=False,
            )
            if lint.returncode != 0:
                raise HarnessError(
                    f"output linter failed for {reply_path}: {lint.stderr.strip()}"
                )
            try:
                lint_findings = json.loads(lint.stdout)
            except json.JSONDecodeError as exc:
                raise HarnessError(f"output linter returned invalid JSON: {exc}") from exc
            cells.append(
                f"CELL {config}/trial-{trial}\n"
                f"REPLY\n{reply.rstrip()}\n"
                "CONSERVATIVE MECHANICAL LINTER FINDINGS (review prompts, not "
                f"automatic failures)\n{json.dumps(lint_findings, indent=2)}\n"
                "RAW HERMES GRADE\n"
                f"{json.dumps(grading['expectations'], indent=2)}"
            )
    expectations = "\n".join(
        f"- {item['id']}: {item['text']}" for item in scenario["expectations"]
    )
    return f"""Act as the verifier for an evaluation grader. The candidate replies,
fixture, expectations, and raw Hermes grades below are public evidence. Find only
demonstrable grading errors: a pass that direct evidence disproves, or a failure
that direct evidence disproves. Do not regrade subjective preferences outside the
expectations. Treat deterministic max-words grades as authoritative and do not
correct them. Return JSON only with this shape:

{{
  "corrections": [
    {{
      "config": "with_skill or without_skill",
      "trial": 1,
      "expectation_id": "exact id",
      "original_passed": true,
      "corrected_passed": false,
      "evidence": "direct quote and reason"
    }}
  ]
}}

Return an empty corrections list if every raw grade is supportable.

SCENARIO: {scenario['name']}

EXPECTATIONS
{expectations}

FIXTURE
{fixture_text(suite_path, scenario).rstrip()}

CELLS
{chr(10).join(cells)}
"""


def validate_corrections(
    value: dict[str, Any],
    suite_path: Path,
    scenario: dict[str, Any],
    runs: Path,
    trials: int,
) -> list[dict[str, Any]]:
    corrections = value.get("corrections")
    if not isinstance(corrections, list):
        raise HarnessError("adjudicator JSON needs a corrections list")
    valid_ids = {item["id"] for item in scenario["expectations"]} | {"max-words"}
    seen: set[tuple[str, int, str]] = set()
    for correction in corrections:
        if not isinstance(correction, dict):
            raise HarnessError("each adjudication correction must be an object")
        config = correction.get("config")
        trial = correction.get("trial")
        expectation_id = correction.get("expectation_id")
        key = (config, trial, expectation_id)
        if config not in CONFIGS or not isinstance(trial, int) or not 1 <= trial <= trials:
            raise HarnessError(f"invalid adjudication cell: {key}")
        if expectation_id not in valid_ids or key in seen:
            raise HarnessError(f"invalid or duplicate adjudication expectation: {key}")
        if expectation_id == "max-words":
            raise HarnessError("adjudicator may not override deterministic max-words")
        if not isinstance(correction.get("original_passed"), bool) or not isinstance(
            correction.get("corrected_passed"), bool
        ):
            raise HarnessError(f"adjudication pass values must be booleans: {key}")
        if correction["original_passed"] == correction["corrected_passed"]:
            raise HarnessError(f"adjudication correction does not change the grade: {key}")
        if not isinstance(correction.get("evidence"), str) or not correction["evidence"].strip():
            raise HarnessError(f"adjudication evidence is empty: {key}")
        grading = read_json(
            runs / scenario["name"] / config / f"trial-{trial}" / "grading.json"
        )
        reply = (
            runs / scenario["name"] / config / f"trial-{trial}" / "reply.md"
        ).read_text(encoding="utf-8")
        validate_saved_grading(
            grading,
            scenario,
            reply,
            sha256_text(grading_prompt(suite_path, scenario, reply)),
        )
        source = {item["id"]: item["passed"] for item in grading["expectations"]}
        if source.get(expectation_id) is not correction["original_passed"]:
            raise HarnessError(f"adjudication original grade does not match source: {key}")
        seen.add(key)
    return corrections


def adjudicate_cells(args: argparse.Namespace) -> None:
    suite_path = args.suite.resolve()
    suite = validate_suite(suite_path)
    skill_text = args.skill.read_text(encoding="utf-8")
    for scenario in suite["scenarios"]:
        for config in CONFIGS:
            for trial in range(1, args.trials + 1):
                cell = args.runs / scenario["name"] / config / f"trial-{trial}"
                metadata = read_json(cell / "generation.json")
                validate_generation_metadata(
                    metadata, suite_path, suite, scenario, config, trial, skill_text
                )
    destination = args.runs / "adjudication"
    for scenario in suite["scenarios"]:
        output_path = destination / f"{scenario['name']}.json"
        if output_path.exists() and not args.overwrite:
            print(f"skip adjudicated scenario: {scenario['name']}")
            continue
        prompt = adjudication_prompt(suite_path, scenario, args.runs, args.trials)
        print(f"adjudicate {scenario['name']}", flush=True)
        result, provider = invoke_claude(prompt, args.model, args.timeout)
        raw = extract_json_object(result)
        corrections = validate_corrections(
            raw, suite_path, scenario, args.runs, args.trials
        )
        record = {
            "schema_version": 1,
            "scenario": scenario["name"],
            "adjudicator_model": sorted(provider.get("modelUsage", {}).keys()),
            "prompt_sha256": sha256_text(prompt),
            "provider_result": {
                "duration_ms": provider.get("duration_ms"),
                "total_cost_usd": provider.get("total_cost_usd"),
                "usage": provider.get("usage"),
            },
            "corrections": corrections,
        }
        atomic_write(output_path, json.dumps(record, indent=2) + "\n")


def summarize_cells(args: argparse.Namespace) -> None:
    suite_path = args.suite.resolve()
    suite = validate_suite(suite_path)
    skill_text = args.skill.read_text(encoding="utf-8")
    overrides: dict[tuple[str, str, int, str], bool] = {}
    correction_count = 0
    adjudication_models: set[str] = set()
    for scenario in suite["scenarios"]:
        path = args.runs / "adjudication" / f"{scenario['name']}.json"
        if not path.is_file():
            if args.require_adjudication:
                raise HarnessError(f"missing adjudication: {path}")
            continue
        record = read_json(path)
        if record.get("scenario") != scenario["name"]:
            raise HarnessError(f"adjudication scenario does not match: {path}")
        models = record.get("adjudicator_model")
        if not isinstance(models, list) or not models or not all(
            isinstance(model, str) and model.strip() for model in models
        ):
            raise HarnessError(f"adjudication needs canonical model metadata: {path}")
        expected_prompt_hash = sha256_text(
            adjudication_prompt(suite_path, scenario, args.runs, args.trials)
        )
        if record.get("prompt_sha256") != expected_prompt_hash:
            raise HarnessError(f"adjudication prompt hash does not match: {path}")
        for model in models:
            adjudication_models.add(str(model))
        corrections = validate_corrections(
            record, suite_path, scenario, args.runs, args.trials
        )
        for correction in corrections:
            key = (
                scenario["name"],
                correction["config"],
                correction["trial"],
                correction["expectation_id"],
            )
            overrides[key] = correction["corrected_passed"]
            correction_count += 1
    primary_path = args.runs / "adjudication" / "primary-verification.json"
    primary_correction_count = 0
    if primary_path.is_file():
        primary = read_json(primary_path)
        if not isinstance(primary.get("verifier"), str) or not primary["verifier"].strip():
            raise HarnessError("primary verification needs a verifier")
        if not isinstance(primary.get("method"), str) or not primary["method"].strip():
            raise HarnessError("primary verification needs a method")
        corrections = primary.get("corrections")
        if not isinstance(corrections, list):
            raise HarnessError("primary verification needs a corrections list")
        scenarios = {scenario["name"]: scenario for scenario in suite["scenarios"]}
        primary_seen: set[tuple[str, str, int, str]] = set()
        for correction in corrections:
            if not isinstance(correction, dict):
                raise HarnessError("primary correction must be an object")
            scenario_name = correction.get("scenario")
            scenario = scenarios.get(scenario_name)
            if scenario is None:
                raise HarnessError(f"unknown primary correction scenario: {scenario_name}")
            config = correction.get("config")
            trial = correction.get("trial")
            expectation_id = correction.get("expectation_id")
            if config not in CONFIGS or not isinstance(trial, int) or not 1 <= trial <= args.trials:
                raise HarnessError("invalid primary correction cell")
            valid_ids = {item["id"] for item in scenario["expectations"]}
            if expectation_id not in valid_ids:
                raise HarnessError("invalid primary correction expectation")
            primary_key = (scenario_name, config, trial, expectation_id)
            if primary_key in primary_seen:
                raise HarnessError("duplicate primary correction")
            grading = read_json(
                args.runs
                / scenario_name
                / config
                / f"trial-{trial}"
                / "grading.json"
            )
            source = {item["id"]: item["passed"] for item in grading["expectations"]}
            expected_original = overrides.get(
                (scenario_name, config, trial, expectation_id),
                source.get(expectation_id),
            )
            if expected_original is not correction.get("original_passed"):
                raise HarnessError("primary correction original grade does not match")
            corrected = correction.get("corrected_passed")
            if not isinstance(corrected, bool) or corrected is expected_original:
                raise HarnessError("primary correction must change a boolean grade")
            if not isinstance(correction.get("evidence"), str) or not correction["evidence"].strip():
                raise HarnessError("primary correction needs evidence")
            overrides[(scenario_name, config, trial, expectation_id)] = corrected
            primary_seen.add(primary_key)
            primary_correction_count += 1
    rows: list[dict[str, Any]] = []
    all_complete = True
    for scenario in suite["scenarios"]:
        for config in CONFIGS:
            scores: list[float] = []
            words: list[int] = []
            for trial in range(1, args.trials + 1):
                cell = args.runs / scenario["name"] / config / f"trial-{trial}"
                grading_path = cell / "grading.json"
                if not grading_path.is_file():
                    all_complete = False
                    continue
                grading = read_json(grading_path)
                reply_path = cell / "reply.md"
                if not reply_path.is_file():
                    raise HarnessError(f"missing generated reply: {reply_path}")
                reply = reply_path.read_text(encoding="utf-8")
                metadata = read_json(cell / "generation.json")
                validate_generation_metadata(
                    metadata, suite_path, suite, scenario, config, trial, skill_text
                )
                expectations = validate_saved_grading(
                    grading,
                    scenario,
                    reply,
                    sha256_text(grading_prompt(suite_path, scenario, reply)),
                )
                verified_passes = 0
                for expectation in expectations:
                    key = (
                        scenario["name"],
                        config,
                        trial,
                        expectation["id"],
                    )
                    verified_passes += int(overrides.get(key, expectation["passed"]))
                scores.append(verified_passes / len(expectations))
                words.append(int(grading["execution_metrics"]["output_words"]))
            rows.append(
                {
                    "scenario": scenario["name"],
                    "config": config,
                    "completed_trials": len(scores),
                    "required_trials": args.trials,
                    "mean_pass_rate": sum(scores) / len(scores) if scores else None,
                    "min_pass_rate": min(scores) if scores else None,
                    "max_pass_rate": max(scores) if scores else None,
                    "mean_words": sum(words) / len(words) if words else None,
                    "min_words": min(words) if words else None,
                    "max_words": max(words) if words else None,
                }
            )
    summary = {
        "schema_version": 1,
        "suite_id": suite["suite_id"],
        "required_trials_per_cell": args.trials,
        "complete": all_complete,
        "adjudication_models": sorted(adjudication_models),
        "adjudication_corrections": correction_count,
        "primary_verification_corrections": primary_correction_count,
        "cells": rows,
    }
    output = json.dumps(summary, indent=2) + "\n"
    if args.output:
        atomic_write(args.output, output)
    print(output, end="")
    if not all_complete:
        raise HarnessError("summary is incomplete")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subcommands = root.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="validate a v2 suite")
    validate.add_argument("--suite", type=Path, required=True)

    run = subcommands.add_parser("run", help="generate fresh Claude response cells")
    run.add_argument("--suite", type=Path, required=True)
    run.add_argument("--skill", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--trials", type=int, default=3)
    run.add_argument("--model", default="sonnet")
    run.add_argument("--timeout", type=int, default=180)
    run.add_argument("--overwrite", action="store_true")

    grade = subcommands.add_parser("grade", help="grade cells with isolated Hermes")
    grade.add_argument("--suite", type=Path, required=True)
    grade.add_argument("--runs", type=Path, required=True)
    grade.add_argument("--trials", type=int, default=3)
    grade.add_argument("--model", default="thinkingmachines/inkling:free")
    grade.add_argument("--timeout", type=int, default=120)
    grade.add_argument("--attempts", type=int, default=3)
    grade.add_argument("--overwrite", action="store_true")

    adjudicate = subcommands.add_parser(
        "adjudicate", help="verify Hermes grades with independent Claude sessions"
    )
    adjudicate.add_argument("--suite", type=Path, required=True)
    adjudicate.add_argument("--runs", type=Path, required=True)
    adjudicate.add_argument("--skill", type=Path, default=Path("SKILL.md"))
    adjudicate.add_argument("--trials", type=int, default=3)
    adjudicate.add_argument("--model", default="sonnet")
    adjudicate.add_argument("--timeout", type=int, default=240)
    adjudicate.add_argument("--overwrite", action="store_true")

    summarize = subcommands.add_parser("summarize", help="summarize graded cells")
    summarize.add_argument("--suite", type=Path, required=True)
    summarize.add_argument("--runs", type=Path, required=True)
    summarize.add_argument("--skill", type=Path, default=Path("SKILL.md"))
    summarize.add_argument("--trials", type=int, default=3)
    summarize.add_argument("--output", type=Path)
    summarize.add_argument("--require-adjudication", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "validate":
            suite = validate_suite(args.suite.resolve())
            print(f"valid: {suite['suite_id']} ({len(suite['scenarios'])} scenarios)")
        elif args.command == "run":
            if args.trials < 1:
                raise HarnessError("--trials must be positive")
            run_cells(args)
        elif args.command == "grade":
            if args.trials < 1:
                raise HarnessError("--trials must be positive")
            if args.attempts < 1:
                raise HarnessError("--attempts must be positive")
            grade_cells(args)
        elif args.command == "adjudicate":
            if args.trials < 1:
                raise HarnessError("--trials must be positive")
            adjudicate_cells(args)
        elif args.command == "summarize":
            summarize_cells(args)
        else:
            raise HarnessError(f"unsupported command: {args.command}")
    except (HarnessError, OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
