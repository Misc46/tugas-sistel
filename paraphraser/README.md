# paraphraser

A small Indonesian prose "humanizer" for LaTeX files. It parses a `.tex` file,
paraphrases the Indonesian prose lines (synonym substitution ranked by a masked
language model, plus a conservative structural pass), and writes a new `.tex`
file with all LaTeX commands, math, URLs, quotes, tabular blocks and TikZ
pictures emitted verbatim.

## Pipeline stages

1. **Parse** (`tex.py`) — line-by-line; only plain prose lines are eligible.
2. **Protect** (`tex.py`) — non-prose spans (`$...$`, ``` ``...'' ```,
   `\cmd{...}`) are hidden behind Private-Use-Area placeholders.
3. **Lexical pass** (`synonyms.py`, `ranker.py`, `lexical.py`) — a fraction
   (`--density`) of dictionary-eligible words is replaced. Candidates come
   from a curated Indonesian synonym map; a masked language model
   (`xlm-roberta-base`) ranks them by how well each fits the sentence.
4. **Structural pass** (`structural.py`) — discourse connectors, safe sentence
   splits and opener variation to break up uniform rhythm.
5. **Restore & verify** (`pipeline.py`) — protected spans are restored, then
   guard checks confirm LaTeX lines are byte-identical and no blacklisted
   technical term was removed.

## Install

```
pip install -r requirements.txt
```

## Usage

```
python -m paraphraser --input examples\input\sinopsis-OSI-TCPIP.tex --out out\revised.tex --density 0.5 --seed 42
```

`--out` defaults to `out\<input-stem>-paraphrased.tex` when omitted.
Other options: `--model` (MLM id, default `xlm-roberta-base`), `--density`
(fraction of eligible words to replace, default 0.35), `--seed` (RNG seed,
default 42).

## Metrics

Compare burstiness (sentence-length coefficient of variation) and
pseudo-perplexity of the prose in two `.tex` files:

```
python -m paraphraser.metrics original.tex revised.tex
```

## Tests

```
python -m unittest discover -s tests -t .
```

## Layout

| Module | Responsibility |
| --- | --- |
| `paraphraser/tex.py` | prose-line detection, protection/restoration of non-prose spans, sentence splitting |
| `paraphraser/synonyms.py` | curated Indonesian synonym map and technical-term blacklist |
| `paraphraser/ranker.py` | masked-LM wrapper that ranks synonym candidates |
| `paraphraser/lexical.py` | word-level synonym replacement |
| `paraphraser/structural.py` | connectors, sentence splits, opener variation |
| `paraphraser/pipeline.py` | paragraph/file processing and post-run verification |
| `paraphraser/metrics.py` | burstiness and pseudo-perplexity measurement |
| `paraphraser/cli.py` | command-line interface |

## Known limitation

Synonym substitution alone barely changes burstiness or pseudo-perplexity —
swapping words keeps sentence lengths and token predictability almost
identical. The structural pass (sentence splits, connectors, opener
variation) is the stronger lever for moving those metrics.
