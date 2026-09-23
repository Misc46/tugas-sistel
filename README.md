# Paraphraser — Bilingual Academic & Prose Humanizer (EN / ID)

A general-purpose academic paraphraser and sentence burstiness optimizer for **LaTeX documents (`.tex`)** and **plain text prose**, supporting both **English** and **Indonesian**.

Designed to humanize machine-uniform prose by increasing structural dynamism and sentence length variance (burstiness), while strictly preserving mathematical formulas, citations, LaTeX commands, and technical terminology.

---

## Key Features

- **🌐 Bilingual Support (English & Indonesian)**: Curated high-precision synonym dictionaries and language-specific structural rules (discourse connectors, sentence splitters, and opener variations).
- **💻 Interactive Web App (`app.html`)**: Single-page application with dark/light themes, instant text editor, file drag-and-drop, and an in-app Quickstart Guide.
- **📊 Live Burstiness Metrics**: Real-time evaluation of sentence length coefficient of variation (CV), average sentence length, standard deviation, and word counts.
- **🔍 Annotated Diff & Side-by-Side Views**: Visual change tracking highlighting lexical substitutions and restructured sentences.
- **🛡️ 100% LaTeX-Safe**: Non-prose elements (`$inline math$`, `\cmd{...}`, quotes, and `tikzpicture` environments) remain byte-identical.
- **⚡ Zero-Dependency Backend**: Local Python HTTP server uses standard library modules with zero pip install requirements for the server layer.
- **🧠 Flexible NLP Engine**: Optional neural masked-LM candidate ranking (`xlm-roberta-base`) with graceful fallback to instant rule-based candidate selection.

---

## Quickstart (Web Application)

Start the local server from the repository root:

```bash
# Standard mode (with XLM-RoBERTa neural LM ranker)
python server.py

# Fast mode (instant startup, rule-based synonym selection)
python server.py --fast
```

The application will launch at `http://127.0.0.1:8000` and automatically open in your default browser.

Alternatively, you can specify a custom port:
```bash
python server.py 8080
```

---

## CLI Usage

You can also use the paraphraser directly from the command line:

```bash
cd paraphraser

# Paraphrase a LaTeX manuscript
python -m paraphraser --input examples/input/sinopsis-OSI-TCPIP.tex \
                      --out out/revised.tex \
                      --density 0.35 \
                      --novelty 3 \
                      --seed 42

# Compare burstiness & perplexity between two files
python -m paraphraser.metrics original.tex revised.tex
```

### CLI Flags

| Flag | Default | Description |
| --- | --- | --- |
| `--input` | *(Required)* | Path to input `.tex` or text file. |
| `--out` | `out/<name>-paraphrased.tex` | Output destination file path. |
| `--density` | `0.35` | Fraction of dictionary-eligible words to substitute (0.1–0.7). |
| `--novelty` | `3` | Sample among ranks 2..N of LM candidates (1 = always top fit). |
| `--seed` | `42` | Random seed for reproducible output. |
| `--model` | `xlm-roberta-base` | Masked LM identifier for candidate ranking. |

---

## Understanding Burstiness

**Burstiness** is defined as the coefficient of variation (CV) of sentence length:

$$\text{Burstiness (CV)} = \frac{\sigma}{\mu} = \frac{\text{Standard Deviation of Sentence Lengths}}{\text{Mean Sentence Length}}$$

- **AI-generated prose** typically exhibits low burstiness ($\text{CV} \approx 0.30 - 0.40$), with unnaturally uniform sentence structures and lengths.
- **Human prose** exhibits higher burstiness ($\text{CV} \ge 0.50$), alternating naturally between punchy short statements and complex clauses.

The engine applies sentence-level splitting, short sentence merging with discourse connectors, and opener variations to raise burstiness towards human baselines.

---

## Project Structure

```
.
├── app.html                    # Single-page web application frontend
├── server.py                   # Root launcher for the local web backend
├── paraphraser/
│   ├── paraphraser/
│   │   ├── tex.py              # Prose detection & LaTeX placeholder protection
│   │   ├── synonyms.py         # Curated EN & ID synonym maps and technical blacklists
│   │   ├── ranker.py           # Masked-LM candidate ranker (XLM-RoBERTa)
│   │   ├── lexical.py          # Word-level replacement pass
│   │   ├── structural.py       # Sentence splits, mergers, discourse connectors
│   │   ├── pipeline.py         # End-to-end document & text processing
│   │   ├── metrics.py          # Burstiness & pseudo-perplexity calculations
│   │   ├── server.py           # Zero-dependency HTTP REST API handler
│   │   └── cli.py              # Command-line interface
│   ├── tests/                  # 39 unit & integration tests
│   ├── examples/               # Sample LaTeX documents
│   └── requirements.txt        # Optional dependencies for neural LM ranking
```

---

## Running Tests

All 39 unit and integration tests run with standard Python `unittest`:

```bash
cd paraphraser
python -m unittest discover -s tests -t .
```

---

## Disclaimer

Commercial AI detectors use non-standardized heuristic classifiers and statistical uniformity models. While increasing burstiness and discourse variation produces more organic sentence rhythms, no detector score should be treated as conclusive evidence of human or machine authorship.
