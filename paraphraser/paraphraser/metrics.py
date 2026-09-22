"""Burstiness and pseudo-perplexity metrics for .tex prose."""
import argparse
import math
import random
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

from .tex import is_prose_line

MODEL = "xlm-roberta-base"


def prose_lines(path):
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    result = []
    in_tikz = False
    for line in lines:
        if "\\begin{tikzpicture}" in line:
            in_tikz = True
        if in_tikz:
            if "\\end{tikzpicture}" in line:
                in_tikz = False
            continue
        if is_prose_line(line):
            result.append(line)
    return result


def clean(text):
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"``.*?''", " ", text)
    text = re.sub(r"\\[A-Za-z]+", " ", text)
    return text


def to_sentences(paras):
    out = []
    for p in paras:
        out.extend(re.split(r"(?<=[.!?])\s+", clean(p)))
    return [s for s in out if s.strip()]


def words(s):
    return len(re.findall(r"[^\W\d_]+", s, re.UNICODE))


def burstiness(sents):
    lens = [words(s) for s in sents]
    n = len(lens)
    mean = sum(lens) / n
    var = sum((x - mean) ** 2 for x in lens) / n
    return mean, math.sqrt(var), math.sqrt(var) / mean, lens


def pseudo_ppl(tok, mdl, sents, max_tokens, chunk=16, per_sentence=64):
    rng = random.Random(0)
    total = 0.0
    count = 0
    for index, s in enumerate(sents):
        if count >= max_tokens:
            break
        ids = tok(s, return_tensors="pt")["input_ids"][0].tolist()
        positions = [
            i for i, t in enumerate(ids)
            if t not in (tok.cls_token_id, tok.sep_token_id, tok.pad_token_id, tok.mask_token_id)
        ]
        if not positions:
            continue
        if len(positions) > per_sentence:
            positions = sorted(rng.sample(positions, per_sentence))
        for start in range(0, len(positions), chunk):
            group = positions[start:start + chunk]
            batch = []
            for p in group:
                m = list(ids)
                m[p] = tok.mask_token_id
                batch.append(m)
            bt = torch.tensor(batch)
            with torch.no_grad():
                logits = mdl(input_ids=bt, attention_mask=torch.ones_like(bt)).logits
            for k, p in enumerate(group):
                total += torch.log_softmax(logits[k, p], dim=-1)[ids[p]].item()
                count += 1
        if index and index % 25 == 0:
            print(f"    ...{count} tokens scored", file=sys.stderr)
    return math.exp(-total / count), count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare burstiness / pseudo-perplexity of two .tex files."
    )
    parser.add_argument("original", type=Path, help="original .tex file")
    parser.add_argument("revised", type=Path, help="revised .tex file")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1200,
        help="cap on tokens scored for pseudo-perplexity (default 1200)",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=4,
        help="only count sentences with at least this many words for filtered burstiness",
    )
    args = parser.parse_args()

    files = [
        ("ORIGINAL", args.original),
        ("REVISED", args.revised),
    ]
    tok = AutoTokenizer.from_pretrained(MODEL)
    mdl = AutoModelForMaskedLM.from_pretrained(MODEL)
    mdl.eval()

    print(f"{'file':10} {'sents':>6} {'mean_w':>7} {'burst':>7} {'burst_fil':>10} {'n_fil':>6} {'pseudoPPL':>10} {'tokens':>7}")
    for tag, path in files:
        sents = to_sentences(prose_lines(path))
        mean, std, cv, lens = burstiness(sents)
        kept = [s for s in sents if words(s) >= args.min_words]
        if len(kept) >= 2:
            fmean, _, fcv, _ = burstiness(kept)
        else:
            fmean, fcv = float("nan"), float("nan")
        ppl, ntok = pseudo_ppl(tok, mdl, sents, args.max_tokens)
        print(f"{tag:10} {len(sents):>6} {mean:>7.1f} {cv:>7.3f} {fcv:>10.3f} {len(kept):>6} {ppl:>10.1f} {ntok:>7}")
        print(f"           sentence word counts: {lens}")
        print(f"           filtered >= {args.min_words} words: n={len(kept)} mean={fmean:.1f} burst={fcv:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
