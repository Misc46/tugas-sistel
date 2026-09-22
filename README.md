# Sinopsis OSI/TCP-IP — Indonesian Paraphraser

Coursework synopsis (Indonesian) about the OSI and TCP/IP models, plus the tooling
built to reduce its AI-detector signal by making the prose statistically less
uniform — without changing any facts or technical terminology.

## Layout

```
.
├── paraphraser/            # the tool (committed)
│   ├── paraphraser/        #   package: tex, synonyms, ranker, lexical,
│   │                       #            structural, pipeline, metrics, cli
│   ├── tests/              #   28 stdlib unittest tests
│   ├── examples/
│   │   ├── input/          #   sample .tex fixture
│   │   └── baseline/       #   fetch script for the human corpus
│   ├── paraphrase.py       #   shim -> python -m paraphraser
│   ├── meter.py            #   shim -> python -m paraphraser.metrics
│   └── out/                #   generated (git-ignored)
├── materials/              # course materials + original source (git-ignored)
├── legacy/                 # earlier IndoBERT/WordNet prototype (git-ignored)
└── output/                 # generated .tex/.pdf artefacts (git-ignored)
```

## Results

Burstiness = coefficient of variation of sentence length (higher = more
human-like). Measured over prose sentences of >= 5 words.

| variant                        | burstiness | vs. original |
| ------------------------------ | ---------- | ------------ |
| original                       | 0.408      | —            |
| v1 synonym substitution        | 0.366      | −10%         |
| v5 automated (S1+S2+S4)        | 0.446      | +9%          |
| **rewritten (discourse-level)**| **0.549**  | **+35%**     |
| human baseline (Wikipedia ID)  | 0.509      | —            |

The discourse-level rewrite is the only variant that clears the human baseline.

## Usage

```bash
cd paraphraser
pip install -r requirements.txt

# paraphrase
python -m paraphraser --input examples/input/sinopsis-OSI-TCPIP.tex \
                      --out out/result.tex \
                      --density 0.5 --seed 42 --novelty 3

# measure burstiness / pseudo-perplexity against a reference
python -m paraphraser.metrics examples/input/sinopsis-OSI-TCPIP.tex out/result.tex \
                      --max-tokens 600 --min-words 5

# tests
python -m unittest discover -s tests -t .
```

Flags: `--density` (fraction of eligible words swapped), `--novelty` (sample
among ranks 2..N of the LM candidates instead of always the best fit),
`--seed` (reproducible), `--min-words` / `--max-tokens` (metric budget).

## How it works

1. **Parse** the `.tex`, protecting LaTeX commands, math, URLs, TikZ picture
   bodies and a technical-term blacklist. Only plain prose is touched.
2. **Substitute** a fraction of eligible words — candidates from a curated
   Indonesian synonym map, ranked for contextual fit by `xlm-roberta-base`.
3. **Restructure** — split long sentences, merge short ones, vary connectors,
   de-parallelise enumerations, then greedily optimise burstiness.

## Known limitations

- Synonym substitution alone barely moves burstiness (it made the first attempt
  *worse*: 0.408 → 0.366). The automated structural pass plateaus around 0.446;
  the real gains come from discourse-level rewriting.
- The pseudo-perplexity metric is register-confounded — the encyclopaedic
  Wikipedia baseline scores *lower* than the student synopsis, so it is reported
  for reference but not optimised against.
- Detector scores are not evidence of authorship; they are unreliable and
  especially poorly validated for Indonesian.
