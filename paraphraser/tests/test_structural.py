import unittest

from paraphraser.structural import _after_connector, _find_split, _split_at


class TestSplitAt(unittest.TestCase):
    def test_split_at_produces_two_sentences(self):
        s = (
            "Layer transport mengatur alur data antar host, "
            "sedangkan layer network menangani pengalamatan logis."
        )
        pos = s.index(", sedangkan")
        head, tail = _split_at(s, pos, 2)
        self.assertEqual(
            head, "Layer transport mengatur alur data antar host."
        )
        self.assertEqual(
            tail, "Sedangkan layer network menangani pengalamatan logis."
        )
        self.assertTrue(head.endswith("."))

    def test_split_at_does_not_double_period(self):
        s = "Angka sudah dihitung?, sedangkan teks belum diverifikasi."
        pos = s.index(", sedangkan")
        head, tail = _split_at(s, pos, 2)
        self.assertEqual(head, "Angka sudah dihitung?")
        self.assertEqual(tail, "Sedangkan teks belum diverifikasi.")


class TestFindSplit(unittest.TestCase):
    def test_short_sentence_without_boundary_returns_none(self):
        self.assertIsNone(_find_split("Kalimat pendek tanpa pembatas."))

    def test_boundary_before_position_50_is_rejected(self):
        sentence = "Kata, sedangkan " + "isi " * 30
        self.assertIsNone(_find_split(sentence))

    def test_valid_boundary_is_returned(self):
        head = "kata " * 12 + "lanjut"
        sentence = (
            head
            + ", sedangkan sisa bagian kalimat dibuat cukup panjang agar "
            "melewati ambang batas posisi."
        )
        self.assertEqual(_find_split(sentence), (sentence.index(", sedangkan"), 2))


class TestAfterConnector(unittest.TestCase):
    def test_ordinary_first_word_is_lower_cased(self):
        self.assertEqual(
            _after_connector("Layer ini mengatur alur data."),
            "layer ini mengatur alur data.",
        )

    def test_osi_keeps_capital(self):
        s = "OSI model punya tujuh layer."
        self.assertEqual(_after_connector(s), s)

    def test_tcp_ip_keeps_capital(self):
        s = "TCP/IP adalah gabungan protokol."
        self.assertEqual(_after_connector(s), s)

    def test_proper_noun_keeps_capital(self):
        s = "Internet berkembang sangat cepat."
        self.assertEqual(_after_connector(s), s)


if __name__ == "__main__":
    unittest.main()
