import unittest

from paraphraser.synonyms import SYNONYMS


class TestSynonyms(unittest.TestCase):
    def test_synonyms_non_empty(self):
        self.assertGreater(len(SYNONYMS), 0)

    def test_no_list_contains_own_key(self):
        for key, values in SYNONYMS.items():
            self.assertNotIn(key, [v.lower() for v in values], key)

    def test_values_are_lower_case(self):
        for key, values in SYNONYMS.items():
            for value in values:
                self.assertTrue(
                    value.islower() or " " in value, f"{key}: {value}"
                )

    def test_known_keys_exist(self):
        self.assertIn("mengatur", SYNONYMS)
        self.assertIn("gampang", SYNONYMS)

    def test_deliberately_removed_key_absent(self):
        self.assertNotIn("langsung", SYNONYMS)


if __name__ == "__main__":
    unittest.main()
