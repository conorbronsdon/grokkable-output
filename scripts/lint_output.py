#!/usr/bin/env python3
"""Conservative mechanical lint for grokkable-output anti-patterns.

The linter only flags patterns that can be detected without reconstructing the
writer's reasoning. Findings are review prompts, not proof that an output is
wrong. In particular, an effort estimate can be detected but cannot be proven
unsourced without the writer's source notes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


WORD_RE = re.compile(r"\b[\w'-]+\b")
SENTENCE_RE = re.compile(r"(?<=[.!?])(?:[\"')\]]+)?\s+")
ARROW_RE = re.compile(r"(?:->|→|⇒)[^\n]*(?:->|→|⇒)")
HEADING_RE = re.compile(
    r"(?m)^\s{0,3}(?:#{1,6}\s+|\*\*[^*\n]{1,80}\*\*(?=\s|$))"
)
DEPTH_OFFER_RE = re.compile(
    r"\b(?:want|would you like|let me know if you(?:'d| would) like|happy to send|"
    r"i can (?:send|provide|share))\b.{0,80}\b(?:breakdown|details?|full list|more)\b",
    re.IGNORECASE,
)
ESTIMATE_RE = re.compile(
    r"\b(?:"
    r"(?:about|around|roughly|approximately|under|less than|more than|up to)\s+"
    r"(?:an?|one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)"
    r"|\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?"
    r")\s*(?:minutes?|hours?|days?|weeks?)\b",
    re.IGNORECASE,
)
TRAILING_RECAP_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s+|\*\*)?(?:tl;?dr|summary|bottom line|in short|recap|proposed plan)\b"
)


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    line: int
    message: str
    excerpt: str


def words(text: str) -> int:
    return len(WORD_RE.findall(text))


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def excerpt(text: str, limit: int = 140) -> str:
    return " ".join(text.split())[:limit]


def paragraphs(text: str) -> list[tuple[int, str]]:
    return [
        (match.start(1), match.group(1).strip())
        for match in re.finditer(r"(?ms)(?:^|\n\s*\n)(.*?)(?=\n\s*\n|\Z)", text)
        if match.group(1).strip()
    ]


def configure_standard_streams() -> None:
    """Keep CLI input/output deterministic on Windows and redirected streams."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="strict")


def lint(text: str) -> list[Finding]:
    findings: list[Finding] = []

    for match in ARROW_RE.finditer(text):
        findings.append(Finding(
            "arrow-chain", "error", line_number(text, match.start()),
            "Rewrite the causal chain as sentences.", excerpt(match.group()),
        ))

    heading_matches = list(HEADING_RE.finditer(text))
    word_count = words(text)
    if len(heading_matches) >= 3 and word_count <= 500:
        first = heading_matches[2]
        findings.append(Finding(
            "heading-density", "warning", line_number(text, first.start()),
            f"{len(heading_matches)} headings or pseudo-headings in {word_count} words; verify that the structure is real.",
            excerpt(first.group()),
        ))

    for offset, paragraph in paragraphs(text):
        paragraph_words = words(paragraph)
        sentence_count = len([s for s in SENTENCE_RE.split(paragraph) if s.strip()])
        if paragraph_words > 100 or sentence_count > 5:
            findings.append(Finding(
                "oversized-block", "warning", line_number(text, offset),
                f"Paragraph has {paragraph_words} words and {sentence_count} sentences; split it without deleting content.",
                excerpt(paragraph),
            ))

    for match in DEPTH_OFFER_RE.finditer(text):
        findings.append(Finding(
            "depth-offer", "warning", line_number(text, match.start()),
            "A depth offer may be replacing the reader's decision or next action.", excerpt(match.group()),
        ))

    for match in ESTIMATE_RE.finditer(text):
        findings.append(Finding(
            "effort-estimate", "review", line_number(text, match.start()),
            "Confirm that this effort estimate is attributed to observed evidence or an identified owner.", excerpt(match.group()),
        ))

    final_quarter = max(0, len(text) * 3 // 4)
    for match in TRAILING_RECAP_RE.finditer(text):
        if match.start() >= final_quarter:
            findings.append(Finding(
                "trailing-recap", "warning", line_number(text, match.start()),
                "A trailing recap may restate a verdict that should already be at the top.", excerpt(match.group()),
            ))

    return sorted(findings, key=lambda item: (item.line, item.rule))


def main(argv: list[str] | None = None) -> int:
    configure_standard_streams()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Markdown/text file; reads stdin when omitted")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-on", choices=("never", "error", "warning", "review"), default="error")
    args = parser.parse_args(argv)

    text = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    findings = lint(text)

    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], indent=2, ensure_ascii=False))
    elif findings:
        for item in findings:
            print(f"{item.severity.upper()} {item.rule} line {item.line}: {item.message}")
            print(f"  {item.excerpt}")
    else:
        print("No mechanical grokkable-output findings.")

    thresholds = {"never": 99, "error": 3, "warning": 2, "review": 1}
    levels = {"error": 3, "warning": 2, "review": 1}
    return int(any(levels[item.severity] >= thresholds[args.fail_on] for item in findings))


if __name__ == "__main__":
    raise SystemExit(main())
