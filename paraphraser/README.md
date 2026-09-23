# paraphraser

An academic prose humanizer and burstiness optimizer for LaTeX documents (`.tex`) and plain text, supporting both **English** and **Indonesian**.

It restructures sentence rhythms (safe splits, merges with discourse connectors, and opener variations) and performs context-aware lexical substitutions while emitting all LaTeX commands, math, URLs, quotes, tabular blocks, and TikZ pictures verbatim.

---

## 🖥️ Web GUI Usage (Recommended)

The easiest and most interactive way to use the tool is via the included single-page web application (`app.html`).

### 1. Start the Local Server

Run the server from either the workspace root or inside `paraphraser/`:

```bash
# Standard mode: loads the XLM-RoBERTa neural LM ranker and opens your browser
python server.py

# Fast mode: starts instantly using rule-based synonym selection (no LM weight loading)
python server.py --fast
```

The web application starts at `http://127.0.0.1:8000` (or the next available port) and will automatically open in your default browser.

### 2. Using the Web Interface (`app.html`)

1. **Select Language Engine**: Use the top-right toggle pills to switch between **English (EN)** and **Indonesian (ID)**.
2. **Choose Input Mode**:
   - **Instant Text**: Paste paragraphs directly into the editor. Live character and word counters update automatically. Click "Samples" to test preloaded examples.
   - **Upload .tex File**: Drag & drop or browse for a `.tex` manuscript.
3. **Tune Parameters (Optional)**: Open the **Advanced Tuning** panel to adjust:
   - **Substitution Density**: Fraction of eligible words to swap (default: `0.35`).
   - **LM Novelty Rank**: Candidate sampling depth (1 = top fit only, 3 = balanced human sampling).
   - **RNG Seed**: Custom or randomized seed for reproducible results.
   - **LaTeX Protection**: Toggle on/off automatic guarding of `$math$`, `\commands`, and quotes.
4. **Click "Paraphrase Prose"** (or press `Ctrl + Enter`).
5. **Inspect Results & Metrics**:
   - **Live Metrics Dashboard**: Evaluates Before vs After **Burstiness (CV)**, Sentence Variance ($\sigma$), and Average Length ($\mu$).
   - **Annotated Diff View**: Strikethroughs and color-coded badges highlight modified prose.
   - **Side-by-Side View**: Compares the original and humanized documents in split columns.
   - **Clean Text View**: Formatted for quick reading.
6. **Export**: Click **Copy to Clipboard** or **Download File** (`.tex` / `.txt`).

---

## ⌨️ CLI Usage

You can also run the pipeline from the command line:

```bash
# Install optional dependencies for neural LM ranking
pip install -r requirements.txt

# Paraphrase a LaTeX manuscript
python -m paraphraser --input examples/input/sinopsis-OSI-TCPIP.tex \
                      --out out/revised.tex \
                      --density 0.35 \
                      --novelty 3 \
                      --seed 42
```

### Options:
- `--input`: Path to input `.tex` or plain text file.
- `--out`: Destination path (defaults to `out/<stem>-paraphrased.tex`).
- `--density`: Fraction of eligible words to replace (default: `0.35`).
- `--novelty`: Sample among ranks 2..N of LM candidates (default: `3`).
- `--seed`: RNG seed for reproducibility (default: `42`).
- `--model`: Masked LM model ID (default: `xlm-roberta-base`).

---

## 📊 Metrics & Burstiness

To evaluate burstiness (sentence-length coefficient of variation) and pseudo-perplexity across two files:

```bash
python -m paraphraser.metrics original.tex revised.tex
```

$$\text{Burstiness (CV)} = \frac{\sigma}{\mu} = \frac{\text{Standard Deviation of Sentence Lengths}}{\text{Mean Sentence Length}}$$

Higher burstiness represents more dynamic, natural human sentence variety, whereas uniform sentence lengths indicate machine-generated text.

---

## 🧪 Tests

All 39 unit and integration tests run with standard Python `unittest`:

```bash
python -m unittest discover -s tests -t .
```

---

## 🏗️ Pipeline Architecture

1. **Parse & Protect** (`tex.py`): Replaces non-prose spans (`$...$`, ``` ``...'' ```, `\cmd{...}`) with Private-Use-Area placeholders so they are never altered.
2. **Lexical Pass** (`synonyms.py`, `ranker.py`, `lexical.py`): Substitutes eligible words using curated English and Indonesian dictionaries, ranked by `xlm-roberta-base`.
3. **Structural Pass** (`structural.py`): Applies language-specific conjunction splits, discourse connectors, short sentence merges, and opener variation.
4. **Restore & Verify** (`pipeline.py`): Restores placeholders and asserts LaTeX structure is byte-identical and technical terms are preserved.
5. **HTTP Server API** (`server.py`): Standard-library REST API serving `app.html` and handling `/api/paraphrase`, `/api/metrics`, and `/api/health`.
