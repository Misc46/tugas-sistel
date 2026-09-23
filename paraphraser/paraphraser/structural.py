"""Structural variation pass."""
from __future__ import annotations

import random
import re

SPLIT_CONJ_RE_ID = re.compile(
    r", (sedangkan|sehingga|tetapi|tapi|namun|lalu|karena|sementara itu|padahal)\b"
)
SPLIT_CONJ_RE_EN = re.compile(
    r", (while|whereas|although|though|but|because|meanwhile|since)\b", re.IGNORECASE
)
SPLIT_CONJ_RE = SPLIT_CONJ_RE_ID

SPLIT_CONJ_RE_ID_DYNAMIC = re.compile(
    r", (sedangkan|sehingga|tetapi|tapi|namun|lalu|karena|sementara itu|padahal|serta|dan|yang mana|di mana)\b", re.IGNORECASE
)
SPLIT_CONJ_RE_EN_DYNAMIC = re.compile(
    r", (while|whereas|although|though|but|because|meanwhile|since|which|who|where|and|so|yet)\b", re.IGNORECASE
)

INVERT_RE_EN = re.compile(r", (because|although|though|while|since)\b", re.IGNORECASE)
INVERT_RE_ID = re.compile(r", (karena|meskipun|walaupun|padahal|sedangkan)\b", re.IGNORECASE)

CONNECTORS_ID = [
    "Selain itu, ",
    "Di samping itu, ",
    "Kemudian, ",
    "Dengan begitu, ",
    "Pada dasarnya, ",
    "Sebagai akibatnya, ",
    "Lebih jauh lagi, ",
    "Tak kalah penting, ",
    "Oleh karena itu, ",
]
CONNECTORS_EN = [
    "Furthermore, ",
    "Moreover, ",
    "In addition, ",
    "Essentially, ",
    "Consequently, ",
    "Notably, ",
    "In particular, ",
    "As a result, ",
    "Importantly, ",
]
CONNECTORS = CONNECTORS_ID

# Words that keep their capital letter even mid-sentence (acronyms / proper nouns).
PROPER = {
    "ethernet", "internet", "tcp", "udp", "ip", "osi", "http", "dns",
    "dhcp", "ftp", "ssh", "qos", "mac", "nic", "youtube", "tcp/ip",
}


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _low(s: str) -> str:
    return s[:1].lower() + s[1:] if s else s


def _boundaries(sentence: str, lang: str = "id", mode: str = "conservative") -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for match in re.finditer(r"; ", sentence):
        candidates.append((match.start(), 2))
    for match in re.finditer(r" [\u2014\u2013] ", sentence):
        candidates.append((match.start(), 3))

    if mode == "conservative":
        split_re = SPLIT_CONJ_RE_EN if lang.lower() == "en" else SPLIT_CONJ_RE_ID
        min_pos = 30
    else:
        split_re = SPLIT_CONJ_RE_EN_DYNAMIC if lang.lower() == "en" else SPLIT_CONJ_RE_ID_DYNAMIC
        min_pos = 20

    for match in split_re.finditer(sentence):
        candidates.append((match.start(), 2))
    return [c for c in candidates if c[0] >= min_pos]


def _find_split(sentence: str, lang: str = "id", mode: str = "conservative") -> tuple[int, int] | None:
    mid = len(sentence) / 2
    best: tuple[int, int] | None = None
    for pos, length in _boundaries(sentence, lang, mode):
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


def _try_invert_clause(sentence: str, rng: random.Random, lang: str = "id") -> str | None:
    """Invert [Head], because [Tail]. into Because [tail], [head]."""
    if "\ue000" in sentence:
        return None
    clean_s = sentence.rstrip()
    if not clean_s.endswith((".", "!", "?")):
        return None
    punct = clean_s[-1]
    body = clean_s[:-1]

    inv_re = INVERT_RE_EN if lang.lower() == "en" else INVERT_RE_ID
    matches = list(inv_re.finditer(body))
    if not matches:
        return None

    m = matches[0]
    head = body[:m.start()].strip()
    conj = m.group(1)
    tail = body[m.end():].strip()

    if _word_count(head) < 3 or _word_count(tail) < 3:
        return None

    return f"{_cap(conj)} {_after_connector(tail)}, {_low(head)}{punct}"


LEAD_CONJUNCTIONS_ID = (
    "dan", "atau", "serta", "tetapi", "tapi", "namun", "melainkan", "sedangkan",
    "sehingga", "lalu", "karena", "padahal", "sementara", "selain", "kemudian",
)
LEAD_CONJUNCTIONS_EN = (
    "and", "or", "but", "while", "although", "though", "because", "meanwhile",
    "furthermore", "however", "moreover", "since", "so", "yet",
)
LEAD_CONJUNCTIONS = LEAD_CONJUNCTIONS_ID


def _try_connector(sentence: str, rng: random.Random, lang: str = "id") -> str | None:
    connectors = CONNECTORS_EN if lang.lower() == "en" else CONNECTORS_ID
    leads = LEAD_CONJUNCTIONS_EN if lang.lower() == "en" else LEAD_CONJUNCTIONS_ID
    if any(sentence.startswith(c) for c in connectors):
        return None
    first = sentence.split(" ", 1)[0].strip(".,;:()!?").lower()
    if first in leads:
        return None
    return rng.choice(connectors) + _after_connector(sentence)


OPENER_SWAPS_ID = (
    ("Layer ini ", "Lapisan ini "),
    ("Di layer ini ", "Pada layer ini "),
    ("Pada TCP/IP, ", "Dalam TCP/IP, "),
    ("Video ini ", "Video tersebut "),
    ("Dari materi ini ", "Dari materi tersebut "),
    ("Hal penting lain ", "Hal penting lainnya "),
    ("Secara umum, ", "Pada dasarnya, "),
    ("Sebagai contoh, ", "Misalnya, "),
    ("Dengan demikian, ", "Akibatnya, "),
)
OPENER_SWAPS_EN = (
    ("This paper ", "The present study "),
    ("In this section, ", "Here, "),
    ("In this paper, ", "Herein, "),
    ("For example, ", "For instance, "),
    ("In other words, ", "Namely, "),
    ("In conclusion, ", "To conclude, "),
    ("On the other hand, ", "Conversely, "),
    ("According to ", "As noted by "),
    ("It is clear that ", "Evidently, "),
    ("To begin with, ", "Initially, "),
)


def _try_opener(sentence: str, lang: str = "id") -> str | None:
    swaps = OPENER_SWAPS_EN if lang.lower() == "en" else OPENER_SWAPS_ID
    for old, new in swaps:
        if sentence.startswith(old):
            return new + sentence[len(old):]
    return None


MERGE_JOINERS_ID = (", sementara itu ", ", sedangkan ", ", sekaligus ", ", dan ", ", sehingga ", ", di samping itu ")
MERGE_JOINERS_EN = (", meanwhile ", ", while ", ", whereas ", ", and ", ", thus ", ", furthermore ")
MERGE_JOINERS = MERGE_JOINERS_ID

FINAL_JOINERS_ID = (", serta ", ", dan juga ", ", maupun ")
FINAL_JOINERS_EN = (", as well as ", ", along with ", ", and also ")
FINAL_JOINERS = FINAL_JOINERS_ID


def _word_count(sentence: str) -> int:
    return len(re.findall(r"[^\W\d_]+", sentence, re.UNICODE))


def _try_merge(first: str, second: str, rng: random.Random, lang: str = "id", max_words: int = 14) -> str | None:
    if _word_count(first) > max_words or _word_count(second) > max_words:
        return None
    if "\ue000" in first or "\ue000" in second:
        return None
    head = first.rstrip()
    if head.endswith((".", "!", "?")):
        head = head[:-1]
    tail = second.strip()
    if tail.endswith((".", "!", "?")):
        tail = tail[:-1]
    joiners = MERGE_JOINERS_EN if lang.lower() == "en" else MERGE_JOINERS_ID
    return head + rng.choice(joiners) + _after_connector(tail)


def _detune_enumeration(sentence: str, rng: random.Random, lang: str = "id") -> str | None:
    match_str = ", and " if lang.lower() == "en" else ", dan "
    joiners = FINAL_JOINERS_EN if lang.lower() == "en" else FINAL_JOINERS_ID
    idx = sentence.rfind(match_str)
    if idx == -1 or sentence[:idx].count(",") < 2:
        return None
    return sentence[:idx] + rng.choice(joiners) + sentence[idx + len(match_str):]


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
    sentences: list[str],
    rng: random.Random,
    stats: dict,
    target: float = 0.6,
    rounds: int = 14,
    lang: str = "id",
    mode: str = "conservative",
) -> list[str]:
    sents = list(sentences)
    min_sentences = 2 if mode in ("dynamic", "aggressive") else 3
    for _ in range(rounds):
        if len(sents) < min_sentences:
            break
        current = _cv(sents)
        if current >= target:
            break
        lens = [_word_count(s) for s in sents]

        moved = False
        long_index = max(range(len(sents)), key=lambda i: lens[i])
        best_split = None
        for pos, length in _boundaries(sents[long_index], lang, mode):
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
            max_merge = 22 if mode == "conservative" else 28
            if lens[short_index] <= max_merge and lens[short_index + 1] <= max_merge:
                merged = _try_merge(sents[short_index], sents[short_index + 1], rng, lang, max_words=max_merge)
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
    sentences: list[str], rng: random.Random, stats: dict, lang: str = "id", mode: str = "dynamic"
) -> list[str]:
    stage: list[str] = []

    # Configure thresholds by mode
    if mode == "conservative":
        split_min_len, split_prob = 90, 0.80
        merge_max_words, merge_prob = 14, 0.55
        connector_prob = 0.25
        opener_prob = 0.30
        invert_prob = 0.0
        burst_target = 0.60
    elif mode == "aggressive":
        split_min_len, split_prob = 42, 0.92
        merge_max_words, merge_prob = 24, 0.75
        connector_prob = 0.55
        opener_prob = 0.55
        invert_prob = 0.45
        burst_target = 0.85
    else:  # dynamic (recommended default)
        split_min_len, split_prob = 55, 0.85
        merge_max_words, merge_prob = 20, 0.65
        connector_prob = 0.40
        opener_prob = 0.45
        invert_prob = 0.35
        burst_target = 0.70

    for sentence in sentences:
        # Clause inversion check
        if invert_prob > 0 and rng.random() < invert_prob:
            inverted = _try_invert_clause(sentence, rng, lang)
            if inverted is not None:
                sentence = inverted
                stats["inversions"] = stats.get("inversions", 0) + 1

        if len(sentence) > split_min_len and rng.random() < split_prob:
            boundary = _find_split(sentence, lang, mode)
            if boundary is not None:
                stage.extend(_split_at(sentence, *boundary))
                stats["splits"] += 1
                continue
        stage.append(sentence)

    merged_out: list[str] = []
    i = 0
    while i < len(stage):
        if i + 1 < len(stage) and rng.random() < merge_prob:
            merged = _try_merge(stage[i], stage[i + 1], rng, lang, max_words=merge_max_words)
            if merged is not None:
                merged_out.append(merged)
                stats["merges"] += 1
                i += 2
                continue
        merged_out.append(stage[i])
        i += 1

    out: list[str] = []
    for sentence in merged_out:
        detuned = _detune_enumeration(sentence, rng, lang)
        if detuned is not None and rng.random() < 0.5:
            sentence = detuned
            stats["enumerations"] += 1

        if len(sentence) < 25 or ("\ue000" in sentence and sentence.count("\ue000") > 2):
            out.append(sentence)
            continue

        if out and rng.random() < connector_prob:
            joined = _try_connector(sentence, rng, lang)
            if joined is not None:
                out.append(joined)
                stats["connectors"] += 1
                continue

        if rng.random() < opener_prob:
            opened = _try_opener(sentence, lang)
            if opened is not None:
                out.append(opened)
                stats["openers"] += 1
                continue

        out.append(sentence)

    return _improve_burstiness(out, rng, stats, target=burst_target, lang=lang, mode=mode)


