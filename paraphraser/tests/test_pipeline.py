import random
import unittest

from paraphraser.pipeline import paraphrase_paragraph
from paraphraser.ranker import Ranker
from paraphraser.tex import is_prose_line


def offline_ranker():
    ranker = Ranker.__new__(Ranker)
    ranker.model = None
    ranker.tok = None
    return ranker


PARAGRAPH = (
    "Model TCP/IP terdiri dari empat layer, sehingga proses pengiriman data "
    "berjalan dengan gampang dan kecepatannya $v = s/t$ selalu terjaga."
)


class TestParaphraseParagraph(unittest.TestCase):
    def test_paragraph_is_prose(self):
        self.assertTrue(is_prose_line(PARAGRAPH))

    def test_paraphrase_smoke(self):
        stats = {
            "prose_lines": 0,
            "changed_lines": 0,
            "replacements": 0,
            "splits": 0,
            "connectors": 0,
            "openers": 0,
        }
        result = paraphrase_paragraph(
            PARAGRAPH, random.Random(42), offline_ranker(), 1.0, stats
        )
        self.assertIsInstance(result, str)
        self.assertTrue(result)
        self.assertIn("TCP/IP", result)
        self.assertIn("$v = s/t$", result)
        self.assertNotEqual(result, PARAGRAPH)
        self.assertGreaterEqual(stats["replacements"], 1)


if __name__ == "__main__":
    unittest.main()
