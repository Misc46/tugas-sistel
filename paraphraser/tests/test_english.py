import random
import unittest

from paraphraser.lexical import replace_words
from paraphraser.pipeline import paraphrase_text
from paraphraser.ranker import Ranker
from paraphraser.structural import structural_pass
from paraphraser.synonyms import (
    BLACKLIST_EN,
    SYNONYMS_EN,
    get_blacklist,
    get_synonyms,
)


def offline_ranker():
    ranker = Ranker.__new__(Ranker)
    ranker.model = None
    ranker.tok = None
    return ranker


class TestEnglish(unittest.TestCase):
    def test_english_synonyms_non_empty(self):
        self.assertGreater(len(SYNONYMS_EN), 50)
        self.assertIn("discuss", SYNONYMS_EN)
        self.assertIn("important", SYNONYMS_EN)
        self.assertIn("explain", SYNONYMS_EN)

    def test_no_list_contains_own_key(self):
        for key, values in SYNONYMS_EN.items():
            self.assertNotIn(key.lower(), [v.lower() for v in values], key)

    def test_blacklist_en(self):
        self.assertIn("tcp", BLACKLIST_EN)
        self.assertIn("ip", BLACKLIST_EN)
        self.assertIn("router", BLACKLIST_EN)

    def test_get_synonyms_and_blacklist_lang_switching(self):
        id_syn = get_synonyms("id")
        en_syn = get_synonyms("en")
        self.assertIn("membahas", id_syn)
        self.assertNotIn("membahas", en_syn)
        self.assertIn("discuss", en_syn)
        self.assertNotIn("discuss", id_syn)

    def test_replace_words_english(self):
        rng = random.Random(42)
        ranker = offline_ranker()
        stats = {"replacements": 0}
        sentence = "This method provides an important solution for the network."
        out = replace_words(sentence, rng, ranker, density=1.0, stats=stats, novelty=1, lang="en")
        self.assertGreater(stats["replacements"], 0)
        self.assertNotEqual(sentence, out)

    def test_structural_pass_english(self):
        rng = random.Random(42)
        stats = {"splits": 0, "connectors": 0, "openers": 0, "merges": 0, "enumerations": 0}
        sentences = [
            "This paper discusses network protocols in detail, although several performance metrics remain unmeasured here.",
            "The results demonstrate high efficiency."
        ]
        out = structural_pass(sentences, rng, stats, lang="en")
        self.assertIsInstance(out, list)
        self.assertGreater(len(out), 0)

    def test_paraphrase_text_english(self):
        rng = random.Random(42)
        ranker = offline_ranker()
        stats = {
            "prose_lines": 0,
            "changed_lines": 0,
            "replacements": 0,
            "splits": 0,
            "connectors": 0,
            "openers": 0,
            "merges": 0,
            "enumerations": 0,
        }
        text = "This paper explains the fundamental method and provides crucial results for future research."
        output, stats, diff = paraphrase_text(text, rng, ranker, density=0.5, stats=stats, lang="en", is_tex=False)
        self.assertIsInstance(output, str)
        self.assertGreater(len(output), 0)
        self.assertEqual(len(diff), 1)


if __name__ == "__main__":
    unittest.main()
