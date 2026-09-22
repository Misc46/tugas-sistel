"""Protection and restoration of non-prose spans, prose-line detection, sentence splitting."""
from __future__ import annotations

import re

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def protect(text: str) -> tuple[str, list[str]]:
    """Replace math / commands / URLs / LaTeX quotes with PUA placeholders."""
    spans: list[str] = []

    def _sub(match: re.Match) -> str:
        spans.append(match.group(0))
        return chr(0xE000 + len(spans) - 1)

    text = re.sub(r"\$[^$]*\$", _sub, text)               # inline math
    text = re.sub(r"``.*?''", _sub, text)                  # LaTeX quotes
    text = re.sub(r"\\[A-Za-z]+\*?(?:\{[^{}]*\})*", _sub, text)  # \cmd{...}
    return text, spans


def restore(text: str, spans: list[str]) -> str:
    for i in range(len(spans) - 1, -1, -1):
        text = text.replace(chr(0xE000 + i), spans[i])
    return text


STRUCTURAL_PREFIXES = (
    "\\documentclass", "\\usepackage", "\\begin", "\\end", "\\section", "\\subsection",
    "\\titleformat", "\\titlespacing", "\\setlength", "\\setlist", "\\hypersetup",
    "\\usetikzlibrary", "\\pagenumbering", "\\vspace", "\\hspace", "\\centering",
    "\\node", "\\draw", "\\path", "\\fill", "\\newcommand", "\\renewcommand", "\\label",
    "\\item[",
)


def is_prose_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("{"):
        return False
    if "&" in line:
        return False
    if stripped.startswith(STRUCTURAL_PREFIXES):
        return False
    plain = re.sub(r"\$[^$]*\$", " ", line)
    plain = re.sub(r"``.*?''", " ", plain)
    plain = re.sub(r"\\[A-Za-z]+\*?(?:\{[^{}]*\})*", " ", plain)
    plain = re.sub(r"[{}]", " ", plain)
    return len(re.findall(r"[^\W\d_]+", plain, re.UNICODE)) >= 5


def split_sentences(text: str) -> list[str]:
    return SENTENCE_SPLIT_RE.split(text)
