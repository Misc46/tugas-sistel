"""Structural variation pass."""
from __future__ import annotations

import random
import re

SPLIT_CONJ_RE = re.compile(
    r", (sedangkan|sehingga|tetapi|tapi|namun|lalu|karena|sementara itu|padahal)\b"
)

CONNECTORS = [
    "Selain itu, ",
    "Di samping itu, ",
    "Kemudian, ",
    "Dengan begitu, ",
    "Pada dasarnya, ",
]

# Words that keep their capital letter even mid-sentence (acronyms / proper nouns).
PROPER = {
    "ethernet", "internet", "tcp", "udp", "ip", "osi", "http", "dns",
    "dhcp", "ftp", "ssh", "qos", "mac", "nic", "youtube", "tcp/ip",
}


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _low(s: str) -> str:
    return s[:1].lower() + s[1:] if s else s


def _boundaries(sentence: str) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for match in re.finditer(r"; ", sentence):
        candidates.append((match.start(), 2))
    for match in re.finditer(r" [\u2014\u2013] ", sentence):
        candidates.append((match.start(), 3))
    for match in SPLIT_CONJ_RE.finditer(sentence):
        candidates.append((match.start(), 2))
    return [c for c in candidates if c[0] >= 30]


def _find_split(sentence: str) -> tuple[int, int] | None:
    mid = len(sentence) / 2
    best: tuple[int, int] | None = None
    for pos, length in _boundaries(sentence):
        if best is None or abs(pos - mid) < abs(best[0] - mid):
            best = (pos, length)
    return best


def _split_at(sentence: str, pos: int, length: int) -> list[str]:
    head = sentence[:pos].rstrip()
    tail = sentence[pos + length:].lstrip()
    if not head.endswith((".", "!", "?")):
        head += "."
    return [head, _cap(tail)]


def _after_connector(sentence: str) -> str:
    first, sep, rest = sentence.partition(" ")
    core = first.strip(".,;:()!?")
    if core.isupper() and len(core) >= 2:
        return sentence
    if core.lower() in PROPER:
        return sentence
    return _low(first) + sep + rest


def _try_connector(sentence: str, rng: random.Random) -> str | None:
    if any(sentence.startswith(c) for c in CONNECTORS):
        return None
    return rng.choice(CONNECTORS) + _after_connector(sentence)


def _try_opener(sentence: str) -> str | None:
    swaps = (
        ("Layer ini ", "Lapisan ini "),
        ("Di layer ini ", "Pada layer ini "),
        ("Pada TCP/IP, ", "Dalam TCP/IP, "),
        ("Video ini ", "Video tersebut "),
        ("Dari materi ini ", "Dari materi tersebut "),
        ("Hal penting lain ", "Hal penting lainnya "),
    )
    for old, new in swaps:
        if sentence.startswith(old):
            return new + sentence[len(old):]
    return None


MERGE_JOINERS = (", sementara itu ", ", sedangkan ", ", sekaligus ", ", dan ", ", sehingga ")
FINAL_JOINERS = (", serta ", ", dan juga ", ", maupun ")


def _word_count(sentence: str) -> int:
    return len(re.findall(r"[^\W\d_]+", sentence, re.UNICODE))


def _try_merge(first: str, second: str, rng: random.Random) -> str | None:
    if _word_count(first) > 14 or _word_count(second) > 14:
        return None
    if "\ue000" in first or "\ue000" in second:
        return None
    head = first.rstrip()
    if head.endswith((".", "!", "?")):
        head = head[:-1]
    tail = second.strip()
    if tail.endswith((".", "!", "?")):
        tail = tail[:-1]
    return head + rng.choice(MERGE_JOINERS) + _after_connector(tail)


def _detune_enumeration(sentence: str, rng: random.Random) -> str | None:
    idx = sentence.rfind(", dan ")
    if idx == -1 or sentence[:idx].count(",") < 2:
        return None
    return sentence[:idx] + rng.choice(FINAL_JOINERS) + sentence[idx + len(", dan "):]


def _cv(sentences: list[str]) -> float:
    lens = [_word_count(s) for s in sentences]
    if len(lens) < 2:
        return 0.0
    mean = sum(lens) / len(lens)
    if mean == 0:
        return 0.0
    var = sum((x - mean) ** 2 for x in lens) / len(lens)
    return (var ** 0.5) / mean


def _improve_burstiness(
    sentences: list[str], rng: random.Random, stats: dict, target: float = 0.6, rounds: int = 14
) -> list[str]:
    sents = list(sentences)
    for _ in range(rounds):
        if len(sents) < 3:
            break
        current = _cv(sents)
        if current >= target:
            break
        lens = [_word_count(s) for s in sents]

        moved = False
        long_index = max(range(len(sents)), key=lambda i: lens[i])
        best_split = None
        for pos, length in _boundaries(sents[long_index]):
            candidate = (sents[:long_index]
                         + _split_at(sents[long_index], pos, length)
                         + sents[long_index + 1:])
            score = _cv(candidate)
            if score > current and (best_split is None or score > best_split[0]):
                best_split = (score, candidate)
        if best_split is not None:
            sents = best_split[1]
            stats["splits"] += 1
            moved = True

        if not moved:
            short_index = min(range(len(sents) - 1), key=lambda i: lens[i] + lens[i + 1])
            if lens[short_index] <= 22 and lens[short_index + 1] <= 22:
                merged = _try_merge(sents[short_index], sents[short_index + 1], rng)
                if merged is not None:
                    candidate = sents[:short_index] + [merged] + sents[short_index + 2:]
                    if _cv(candidate) > current:
                        sents = candidate
                        stats["merges"] += 1
                        moved = True

        if not moved:
            break
    return sents


def structural_pass(
    sentences: list[str], rng: random.Random, stats: dict
) -> list[str]:
    stage: list[str] = []
    for sentence in sentences:
        if len(sentence) > 90 and rng.random() < 0.8:
            boundary = _find_split(sentence)
            if boundary is not None:
                stage.extend(_split_at(sentence, *boundary))
                stats["splits"] += 1
                continue
        stage.append(sentence)

    merged_out: list[str] = []
    i = 0
    while i < len(stage):
        if i + 1 < len(stage) and rng.random() < 0.55:
            merged = _try_merge(stage[i], stage[i + 1], rng)
            if merged is not None:
                merged_out.append(merged)
                stats["merges"] += 1
                i += 2
                continue
        merged_out.append(stage[i])
        i += 1

    out: list[str] = []
    for sentence in merged_out:
        detuned = _detune_enumeration(sentence, rng)
        if detuned is not None and rng.random() < 0.5:
            sentence = detuned
            stats["enumerations"] += 1

        if len(sentence) < 25 or ("\ue000" in sentence and sentence.count("\ue000") > 2):
            out.append(sentence)
            continue

        if out and rng.random() < 0.25:
            joined = _try_connector(sentence, rng)
            if joined is not None:
                out.append(joined)
                stats["connectors"] += 1
                continue

        if rng.random() < 0.3:
            opened = _try_opener(sentence)
            if opened is not None:
                out.append(opened)
                stats["openers"] += 1
                continue

        out.append(sentence)

    return _improve_burstiness(out, rng, stats)
