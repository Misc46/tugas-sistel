import random
import unittest

from paraphraser.lexical import replace_words
from paraphraser.ranker import Ranker


def offline_ranker():
    ranker = Ranker.__new__(Ranker)
    ranker.model = None
    ranker.tok = None
    return ranker


class TestReplaceWords(unittest.TestCase):
    def test_density_zero_returns_sentence_unchanged(self):
        sentence = "Model OSI membahas tujuh layer yang saling terhubung dengan gampang."
        stats = {"replacements": 0}
        out = replace_words(sentence, random.Random(42), offline_ranker(), 0.0, stats)
        self.assertEqual(out, sentence)
        self.assertEqual(stats["replacements"], 0)

    def test_protected_pua_tokens_are_never_modified(self):
        sentence = "protokol \ue000 mengatur pengiriman data \ue000."
        stats = {"replacements": 0}
        out = replace_words(sentence, random.Random(7), offline_ranker(), 1.0, stats)
        self.assertEqual(out.count("\ue000"), 2)
        self.assertIn("\ue000", out.split(" "))
        self.assertIn("\ue000.", out.split(" "))

    def test_blacklisted_term_is_not_replaced(self):
        sentence = "setiap layer punya tugas berbeda."
        stats = {"replacements": 0}
        out = replace_words(sentence, random.Random(0), offline_ranker(), 1.0, stats)
        self.assertIn("layer", out.split(" "))


if __name__ == "__main__":
    unittest.main()
