#!/usr/bin/env python3
"""Run the Paraphraser web application backend."""
import sys
from pathlib import Path

# Add paraphraser package to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "paraphraser"))

from paraphraser.server import run_server

if __name__ == "__main__":
    port = 8000
    for arg in sys.argv[1:]:
        if arg.isdigit():
            port = int(arg)
    use_lm = "--no-lm" not in sys.argv and "--fast" not in sys.argv
    run_server(port=port, use_lm=use_lm)

