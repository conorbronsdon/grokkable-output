#!/usr/bin/env python3
"""Conservative mechanical lint for grokkable-output anti-patterns.

The linter only flags patterns that can be detected without reconstructing the
writer's reasoning. Findings are review prompts, not proof that an output is
wrong. In particular, an effort estimate can be detected but cannot be proven
unsourced without the writer's source notes.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


WORD_RE = re.compile(r"\b[\w'-]+\b")
SENTENCE_RE = re.compile(r"(?<=[.!?])(?:[\"')\]]+)?\s+")
ARROW_RE = re.compile(
    r"(?:->|→|⇒)"
    r"(?:(?![.!?](?:[\"')\]]+)?\s+|,\s+(?:while|whereas)\b)[^;|\n])*"
    r"(?:->|→|⇒)"
)
SEMICOLON_CHAIN_RE = re.compile(
    r"(?:->|\u2192|\u21d2)\s*(?:[\w.-]+\s+)*(?P<bridge>[\w.-]+)\s*;\s*"
    r"(?P=bridge)\b[^;|\n]*?(?:->|\u2192|\u21d2)",
    re.IGNORECASE,
)
HEADING_RE = re.compile(
    r"(?m)^[ \t]{0,3}(?:#{1,6}\s+|\*\*[^*\n]{1,80}\*\*(?=\s|$))"
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
    r"|(?:(?:takes?|requires?|needs?|costs?)|(?:will|would|should|could)\s+take)\s+"
    r"over\s+(?:an?|one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)"
    r"|\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?"
    r")\s*(?:minutes?|hours?|days?|weeks?)\b",
    re.IGNORECASE,
)
TRAILING_RECAP_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s+|\*\*)?(?:tl;?dr|summary|bottom line|in short|recap|proposed plan)\b"
)
FENCE_RE = re.compile(
    r"^(?P<container>(?:[ \t]{0,3}>[ \t]?)*)(?:[ \t]{0,3})"
    r"(?P<fence>`{3,}|~{3,})"
)
STRUCTURED_LINE_RE = re.compile(
    r"^(?:"
    r"[ \t]{0,3}(?:#{1,6}\s+|>\s?).*"
    r"|[ \t]*(?:[-+*]|\d+[.)])\s+.*"
    r"|[ \t]*\|.*\|[ \t]*"
    r")$"
)
LIST_LINE_RE = re.compile(
    r"^[ \t]*(?:[-+*]|\d+[.)])\s+(?P<content>.*)$"
)
BLOCKQUOTE_INDENTED_CODE_RE = re.compile(
    r"^(?:[ \t]{0,3}>[ \t]?)+(?: {4}|\t)"
)
LIST_MARKER_RE = re.compile(
    r"^(?P<container>(?:[ \t]{0,3}>[ \t]?)*)(?P<indent>[ \t]*)"
    r"(?:[-+*]|\d+[.)])\s+"
)
HTML_CODE_RE = re.compile(
    r"(?is)<(?P<tag>pre|code)\b[^>]*>.*?</(?P=tag)\s*>"
)
AUTOLINK_RE = re.compile(r"(?i)<(?:https?://|mailto:)[^>\n]+>")
RAW_URL_RE = re.compile(r"(?i)\bhttps?://[^\s<>()]+")
REFERENCE_URL_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(?P<url><?[^\s>]+>?)"
)
OBSERVED_DURATION_RE = re.compile(
    r"(?:"
    r"\b(?:completed|finished)\b[^.;]{0,60}\b(?:in|after|within)\s*"
    r"|\b(?:took|lasted)\s*"
    r"|\b(?:ran|held|stayed|remained|monitored|observed|measured)\b.{0,60}"
    r"\b(?:for|over|across)\s*"
    r"|\b(?:(?:is|are|was|were)\s+)?(?:retained|supported)\s+for\s*"
    r")$",
    re.IGNORECASE,
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


def excerpt(text: str, limit: int = 140) -> str:
    return " ".join(text.split())[:limit]


def paragraphs(text: str) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    for match in re.finditer(r"(?ms)(?:^|\n\s*\n)(.*?)(?=\n\s*\n|\Z)", text):
        raw_block = match.group(1)
        leading = len(raw_block) - len(raw_block.lstrip())
        block = raw_block.strip()
        if not block:
            continue
        lines = [line for line in block.splitlines() if line.strip()]
        if lines and all(STRUCTURED_LINE_RE.match(line) for line in lines):
            line_offset = match.start(1) + leading
            for line in block.splitlines(keepends=True):
                item = LIST_LINE_RE.match(line.rstrip("\r\n"))
                if item and item.group("content").strip():
                    content = item.group("content").strip()
                    content_leading = len(item.group("content")) - len(item.group("content").lstrip())
                    blocks.append((
                        line_offset + item.start("content") + content_leading,
                        content,
                    ))
                line_offset += len(line)
            continue
        blocks.append((match.start(1) + leading, block))
    return blocks


def mask_range(output: list[str], text: str, start: int, end: int) -> None:
    """Mask one source range without changing offsets or line endings."""
    for index in range(start, end):
        if text[index] not in "\r\n":
            output[index] = " "


def mask_nonprose_markdown(text: str) -> str:
    """Mask Markdown code and link destinations while preserving source offsets."""
    output = list(text)
    fence_character: str | None = None
    fence_length = 0
    fence_quote_depth = 0
    active_list_indents: list[int] = []
    active_list_quote_depth: int | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = FENCE_RE.match(line)
        if fence_character is not None and fence_quote_depth:
            quote_prefix = re.match(r"^(?:[ \t]{0,3}>[ \t]?)*", line)
            current_depth = quote_prefix.group().count(">") if quote_prefix else 0
            if current_depth < fence_quote_depth:
                fence_character = None
                fence_length = 0
                fence_quote_depth = 0
        if fence_character is None and marker:
            fence_character = marker.group("fence")[0]
            fence_length = len(marker.group("fence"))
            fence_quote_depth = marker.group("container").count(">")
            mask_range(output, text, offset, offset + len(line))
            offset += len(line)
            continue
        if fence_character is not None:
            mask_range(output, text, offset, offset + len(line))
            if (
                marker
                and marker.group("fence")[0] == fence_character
                and len(marker.group("fence")) >= fence_length
                and not line[marker.end():].strip()
            ):
                fence_character = None
                fence_length = 0
                fence_quote_depth = 0
            offset += len(line)
            continue
        list_marker = LIST_MARKER_RE.match(line)
        nested_list_item = False
        if list_marker:
            quote_depth = list_marker.group("container").count(">")
            indent = len(list_marker.group("indent").expandtabs(4))
            if quote_depth != active_list_quote_depth:
                active_list_indents = []
            if indent <= 3:
                active_list_indents = [indent]
                active_list_quote_depth = quote_depth
            else:
                parents = [item for item in active_list_indents if item < indent]
                nested_list_item = bool(parents)
                if nested_list_item:
                    active_list_indents = [*parents, indent]
                    active_list_quote_depth = quote_depth
        elif not line.strip():
            active_list_indents = []
            active_list_quote_depth = None
        else:
            quote_prefix = re.match(r"^(?:[ \t]{0,3}>[ \t]?)*", line)
            quote_depth = quote_prefix.group().count(">") if quote_prefix else 0
            content = line[quote_prefix.end():] if quote_prefix else line
            raw_indent = content[:len(content) - len(content.lstrip(" \t"))]
            indent = len(raw_indent.expandtabs(4))
            if quote_depth != active_list_quote_depth or not active_list_indents:
                active_list_indents = []
                active_list_quote_depth = None
            elif indent <= active_list_indents[0]:
                active_list_indents = []
                active_list_quote_depth = None

        if (
            re.match(r"^(?: {4}|\t)", line)
            or BLOCKQUOTE_INDENTED_CODE_RE.match(line)
        ) and not nested_list_item:
            mask_range(output, text, offset, offset + len(line))
        offset += len(line)

    for match in HTML_CODE_RE.finditer(text):
        mask_range(output, text, match.start(), match.end())

    # Markdown code spans pair delimiter runs of the same length. Pairing is
    # linear in the number of runs and covers multi-backtick spans without a
    # backtracking-heavy regular expression.
    pending_ticks: dict[int, tuple[int, int]] = {}
    for marker in re.finditer(r"`+", text):
        backslashes = 0
        index = marker.start() - 1
        while index >= 0 and text[index] == "\\":
            backslashes += 1
            index -= 1
        if backslashes % 2 or output[marker.start()] == " ":
            continue
        length = len(marker.group())
        opening = pending_ticks.get(length)
        if opening is None:
            pending_ticks[length] = (marker.start(), marker.end())
        elif re.search(r"\n[ \t]*\n", text[opening[1]:marker.start()]) or any(
            output[position] == " " and not text[position].isspace()
            for position in range(opening[1], marker.start())
        ):
            # Inline code cannot cross a Markdown block boundary. A masked
            # block between equal tick runs makes the later run a new opener.
            pending_ticks[length] = (marker.start(), marker.end())
        else:
            pending_ticks.pop(length)
            mask_range(output, text, opening[0], marker.end())

    for match in AUTOLINK_RE.finditer(text):
        mask_range(output, text, match.start(), match.end())
    for match in RAW_URL_RE.finditer(text):
        mask_range(output, text, match.start(), match.end())
    for match in REFERENCE_URL_RE.finditer(text):
        mask_range(output, text, match.start("url"), match.end("url"))

    # Mask inline-link destinations, including balanced parentheses in URLs.
    cursor = 0
    while True:
        start = text.find("](", cursor)
        if start < 0:
            break
        index = start + 2
        depth = 1
        escaped = False
        while index < len(text) and depth:
            char = text[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char.isspace():
                break
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            index += 1
        if depth == 0:
            mask_range(output, text, start + 2, index - 1)
            cursor = index
        else:
            cursor = start + 2

    return "".join(output)


def is_observed_duration(text: str, start: int) -> bool:
    """Return whether the matched duration sits in an observed-result clause."""
    clause_start = max(
        text.rfind(".", 0, start),
        text.rfind("\n", 0, start),
        text.rfind(";", 0, start),
    ) + 1
    prefix = text[clause_start:start]
    if re.search(
        r"\b(?:will|would|should|could)\s+(?:take|require|need|cost)\b",
        prefix,
        re.IGNORECASE,
    ):
        return False
    return bool(OBSERVED_DURATION_RE.search(prefix))


def configure_standard_streams() -> None:
    """Keep CLI input/output deterministic on Windows and redirected streams."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="strict")


def lint(text: str) -> list[Finding]:
    findings: list[Finding] = []
    prose = mask_nonprose_markdown(text)
    line_starts = [0, *(match.end() for match in re.finditer("\n", text))]

    def source_line(offset: int) -> int:
        return bisect.bisect_right(line_starts, offset)

    for match in ARROW_RE.finditer(prose):
        findings.append(Finding(
            "arrow-chain", "error", source_line(match.start()),
            "Rewrite the causal chain as sentences.",
            excerpt(text[match.start():match.end()]),
        ))

    for match in SEMICOLON_CHAIN_RE.finditer(prose):
        findings.append(Finding(
            "arrow-chain", "error", source_line(match.start()),
            "Rewrite the causal chain as sentences.",
            excerpt(text[match.start():match.end()]),
        ))

    heading_matches = list(HEADING_RE.finditer(prose))
    word_count = words(prose)
    if len(heading_matches) >= 3 and word_count <= 500:
        first = heading_matches[2]
        findings.append(Finding(
            "heading-density", "warning", source_line(first.start()),
            f"{len(heading_matches)} headings or pseudo-headings in {word_count} words; verify that the structure is real.",
            excerpt(text[first.start():first.end()]),
        ))

    for offset, paragraph in paragraphs(prose):
        paragraph_words = words(paragraph)
        sentence_count = len([s for s in SENTENCE_RE.split(paragraph) if s.strip()])
        if paragraph_words > 100 or sentence_count > 5:
            findings.append(Finding(
                "oversized-block", "warning", source_line(offset),
                f"Paragraph has {paragraph_words} words and {sentence_count} sentences; split it without deleting content.",
                excerpt(text[offset:offset + len(paragraph)]),
            ))

    for match in DEPTH_OFFER_RE.finditer(prose):
        findings.append(Finding(
            "depth-offer", "warning", source_line(match.start()),
            "A depth offer may be replacing the reader's decision or next action.",
            excerpt(text[match.start():match.end()]),
        ))

    for match in ESTIMATE_RE.finditer(prose):
        if is_observed_duration(prose, match.start()):
            continue
        findings.append(Finding(
            "effort-estimate", "review", source_line(match.start()),
            "Confirm that this effort estimate is attributed to observed evidence or an identified owner.",
            excerpt(text[match.start():match.end()]),
        ))

    final_quarter = max(0, len(prose) * 3 // 4)
    for match in TRAILING_RECAP_RE.finditer(prose):
        if match.start() >= final_quarter:
            findings.append(Finding(
                "trailing-recap", "warning", source_line(match.start()),
                "A trailing recap may restate a verdict that should already be at the top.",
                excerpt(text[match.start():match.end()]),
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
