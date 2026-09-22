"""Word-level hybrid replacement."""
from __future__ import annotations

import random
import re

from .ranker import Ranker
from .synonyms import BLACKLIST, SYNONYMS

MASK_PLACEHOLDER_RE = re.compile(r"^(\W*)(\w+)(\W*)$", re.UNICODE)


def replace_words(
    sentence: str,
    rng: random.Random,
    ranker: Ranker,
    density: float,
    stats: dict,
    novelty: int = 3,
) -> str:
    tokens = sentence.split(" ")
    out: list[str] = []
    replaced_here = 0

    for index, token in enumerate(tokens):
        if "\ue000" in token or replaced_here >= 3:
            out.append(token)
            continue
        m = MASK_PLACEHOLDER_RE.match(token)
        if not m:
            out.append(token)
            continue

        lead, core, tail = m.groups()
        key = core.lower()
        if (
            key not in SYNONYMS
            or key in BLACKLIST
            or len(key) < 4
            or rng.random() >= density
        ):
            out.append(token)
            continue

        candidates = SYNONYMS[key]
        chosen = None

        if ranker.available:
            masked_tokens = list(tokens)
            masked_tokens[index] = lead + ranker.tok.mask_token + tail
            masked_sentence = " ".join(masked_tokens)
            scores = ranker.rank(masked_sentence, candidates)
            ranked = sorted(scores.items(), key=lambda kv: -kv[1])
            ranked = [(c, s) for c, s in ranked if c.lower() != key]
            if ranked:
                if novelty <= 1 or len(ranked) == 1:
                    chosen = ranked[0][0]
                else:
                    window = ranked[1:novelty + 1] or ranked[1:2]
                    chosen = rng.choice([c for c, _ in window])

        if chosen is None:
            pool = [c for c in candidates if c.lower() != key]
            if not pool:
                out.append(token)
                continue
            chosen = rng.choice(pool)

        if core[:1].isupper():
            chosen = chosen[:1].upper() + chosen[1:]

        out.append(lead + chosen + tail)
        replaced_here += 1
        stats["replacements"] += 1

    return " ".join(out)
