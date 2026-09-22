"""Command-line interface for the paraphraser."""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from .pipeline import process_file, verify
from .ranker import DEFAULT_MODEL, Ranker
from .tex import is_prose_line


def main() -> int:
    parser = argparse.ArgumentParser(description="Indonesian prose humanizer for LaTeX files.")
    parser.add_argument("--input", type=Path, required=True, help="input .tex file")
    parser.add_argument("--out", type=Path, default=None,
                        help="output .tex file (default: out/<input-stem>-paraphrased.tex)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"MLM id (default {DEFAULT_MODEL})")
    parser.add_argument("--density", type=float, default=0.35, help="fraction of eligible words to replace")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    parser.add_argument("--novelty", type=int, default=3,
                        help="sample among ranks 2..N of the LM candidates (1 = always best-fit)")
    args = parser.parse_args()

    if args.novelty < 1:
        print("error: --novelty must be >= 1", file=sys.stderr)
        return 2

    if args.out is None:
        args.out = Path("out") / f"{args.input.stem}-paraphrased.tex"

    if not args.input.is_file():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    rng = random.Random(args.seed)
    print("=" * 78)
    print(f"Paraphrase  |  input={args.input.name}  out={args.out.name}")
    print(f"config      |  model={args.model}  density={args.density}  seed={args.seed}  novelty={args.novelty}")
    print("=" * 78)

    ranker = Ranker(args.model)
    original_lines, output_lines, stats = process_file(
        args.input, rng, ranker, args.density, args.novelty
    )

    print("\n" + "-" * 78)
    print("PROSE DIFF (original vs paraphrased)")
    print("-" * 78)
    # rebuild report from the two line lists for accurate pairing
    report = []
    for a, b in zip(original_lines, output_lines):
        if a != b and is_prose_line(a):
            report.append(f"ORIGINAL   : {a}\nPARAPHRASED: {b}\n")
    if report:
        print("\n".join(report))
    else:
        print("(no prose lines changed)")

    args.out.write_text("\n".join(output_lines), encoding="utf-8")

    print("=" * 78)
    print("VERIFICATION")
    print("=" * 78)
    for line in verify(original_lines, output_lines, stats):
        print(line)

    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"  prose lines processed : {stats['prose_lines']}")
    print(f"  prose lines changed   : {stats['changed_lines']}")
    print(f"  word replacements     : {stats['replacements']}")
    print(f"  structural changes    : splits={stats['splits']} "
          f"connectors={stats['connectors']} openers={stats['openers']} "
          f"merges={stats['merges']} enumerations={stats['enumerations']}")
    print(f"  output written        : {args.out}")
    print("=" * 78)
    return 0
