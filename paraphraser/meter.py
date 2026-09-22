#!/usr/bin/env python3
"""Backward-compat shim: delegates to paraphraser.metrics.main."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paraphraser.metrics import main

if __name__ == "__main__":
    raise SystemExit(main())
