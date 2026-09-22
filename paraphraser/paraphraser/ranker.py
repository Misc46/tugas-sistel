"""Masked-LM candidate ranker."""
from __future__ import annotations

import sys

DEFAULT_MODEL = "xlm-roberta-base"


class Ranker:
    """Wraps the masked-LM so it is loaded exactly once and can degrade."""

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        self.tok = None
        self.model = None
        try:
            import torch
            from transformers import AutoModelForMaskedLM, AutoTokenizer

            self._torch = torch
            self.tok = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForMaskedLM.from_pretrained(model_id)
            self.model.eval()
            print(
                f"[ranker] loaded {model_id} (mask token = {self.tok.mask_token!r})",
                file=sys.stderr,
            )
        except Exception as exc:  # pragma: no cover - environment dependent
            print(f"[ranker] WARNING: could not load {model_id}: {exc}", file=sys.stderr)
            print("[ranker] falling back to random candidate choice.", file=sys.stderr)

    @property
    def available(self) -> bool:
        return self.model is not None and self.tok is not None

    def rank(self, masked_sentence: str, candidates: list[str]) -> dict[str, float]:
        """Return {candidate: mean log-prob at the mask position}."""
        if not self.available:
            return {}
        torch = self._torch
        tok = self.tok
        enc = tok(masked_sentence, return_tensors="pt")
        ids = enc["input_ids"][0].tolist()
        if tok.mask_token_id not in ids:
            return {}
        mask_pos = ids.index(tok.mask_token_id)
        with torch.no_grad():
            logits = self.model(**enc).logits[0]
        log_probs = torch.log_softmax(logits[mask_pos], dim=-1)

        scores: dict[str, float] = {}
        for cand in candidates:
            sub = tok(cand, add_special_tokens=False)["input_ids"]
            if not sub:
                continue
            scores[cand] = sum(log_probs[t].item() for t in sub) / len(sub)
        return scores
