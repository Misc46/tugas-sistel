"""Paragraph and file-level paraphrase pipeline."""
from __future__ import annotations

import random
from pathlib import Path

from .lexical import replace_words
from .ranker import Ranker
from .structural import structural_pass
from .synonyms import BLACKLIST
from .tex import is_prose_line, protect, restore, split_sentences


def paraphrase_paragraph(
    paragraph: str,
    rng: random.Random,
    ranker: Ranker,
    density: float,
    stats: dict,
    novelty: int = 3,
) -> str:
    masked, spans = protect(paragraph)
    sentences = split_sentences(masked)
    sentences = [replace_words(s, rng, ranker, density, stats, novelty) for s in sentences]
    sentences = structural_pass(sentences, rng, stats)
    return restore(" ".join(sentences), spans)


def process_file(
    path: Path, rng: random.Random, ranker: Ranker, density: float, novelty: int = 3
) -> tuple[list[str], list[str], dict]:
    original_lines = path.read_text(encoding="utf-8").split("\n")
    output_lines: list[str] = []
    report: list[str] = []
    stats = {
        "prose_lines": 0,
        "changed_lines": 0,
        "replacements": 0,
        "splits": 0,
        "connectors": 0,
        "openers": 0,
        "merges": 0,
        "enumerations": 0,
    }

    in_tikz = False
    for line in original_lines:
        if "\\begin{tikzpicture}" in line:
            in_tikz = True
        if in_tikz:
            output_lines.append(line)
            if "\\end{tikzpicture}" in line:
                in_tikz = False
            continue
        if not is_prose_line(line):
            output_lines.append(line)
            continue

        stats["prose_lines"] += 1
        new_line = paraphrase_paragraph(line, rng, ranker, density, stats, novelty)
        if new_line != line:
            stats["changed_lines"] += 1
            report.append(f"ORIGINAL   : {line}\nPARAPHRASED: {new_line}")
        output_lines.append(new_line)

    return original_lines, output_lines, stats


def verify(original_lines: list[str], output_lines: list[str], stats: dict) -> list[str]:
    checks: list[str] = []

    def ok(cond: bool, msg: str) -> None:
        checks.append(f"  [{'OK ' if cond else 'FAIL'}] {msg}")

    ok(len(original_lines) == len(output_lines),
       f"line count preserved ({len(original_lines)} -> {len(output_lines)})")

    guard_tokens = ("\\begin{tikzpicture}", "\\end{tikzpicture}", "\\section*",
                    "\\subsection*", "\\documentclass", "\\usepackage", "\\url")
    identical = True
    for a, b in zip(original_lines, output_lines):
        if any(tok in a for tok in guard_tokens) and a != b:
            identical = False
            checks.append(f"  [FAIL] LaTeX guard line changed: {a!r}")
    ok(identical, "tikz / section / preamble / url lines byte-identical")

    original_blob = " ".join(original_lines).lower()
    output_blob = " ".join(output_lines).lower()
    touched = [w for w in BLACKLIST if f" {w} " in original_blob and f" {w} " not in output_blob]
    ok(not touched, f"no blacklisted technical term removed (offenders: {touched})")

    ok(stats["replacements"] > 0, f"word replacements performed: {stats['replacements']}")
    structural = (stats["splits"] + stats["connectors"] + stats["openers"]
                  + stats.get("merges", 0) + stats.get("enumerations", 0))
    ok(structural > 0, f"structural changes performed: {structural}")
    return checks
