import unittest

from paraphraser.tex import is_prose_line, protect, restore


class TestProtectRestore(unittest.TestCase):
    def test_protect_masks_inline_math(self):
        text = "kecepatan $c = 3$ saja"
        masked, spans = protect(text)
        self.assertEqual(spans, ["$c = 3$"])
        self.assertNotIn("$", masked)
        self.assertIn("\ue000", masked)
        self.assertEqual(restore(masked, spans), text)

    def test_protect_masks_latex_quotes(self):
        text = "Ia berkata ``hello world'' tadi"
        masked, spans = protect(text)
        self.assertEqual(spans, ["``hello world''"])
        self.assertNotIn("``", masked)
        self.assertEqual(restore(masked, spans), text)

    def test_protect_masks_commands(self):
        text = "data dikirim \\textbf{cepat} sekali"
        masked, spans = protect(text)
        self.assertEqual(spans, ["\\textbf{cepat}"])
        self.assertNotIn("\\textbf", masked)
        self.assertEqual(restore(masked, spans), text)

    def test_protect_multiple_spans_in_order(self):
        text = "nilai $x_1$ dan ``quote'' serta \\emph{teks} lain"
        masked, spans = protect(text)
        self.assertEqual(spans, ["$x_1$", "``quote''", "\\emph{teks}"])
        self.assertEqual(restore(masked, spans), text)

    def test_placeholders_use_pua_codepoints(self):
        masked, spans = protect("$a$ ``b'' \\c{d}")
        self.assertEqual(len(spans), 3)
        self.assertIn(chr(0xE000), masked)
        self.assertIn(chr(0xE001), masked)
        self.assertIn(chr(0xE002), masked)
        for ch in masked:
            if ord(ch) >= 0xE000:
                self.assertLessEqual(ord(ch), 0xF8FF)


class TestIsProseLine(unittest.TestCase):
    def test_plain_indonesian_sentence_is_prose(self):
        self.assertTrue(is_prose_line("Model OSI terdiri dari tujuh layer."))

    def test_backslash_line_is_not_prose(self):
        self.assertFalse(is_prose_line("\\section*{Sinopsis}"))

    def test_ampersand_line_is_not_prose(self):
        self.assertFalse(is_prose_line("kolom pertama & kolom kedua"))

    def test_blank_line_is_not_prose(self):
        self.assertFalse(is_prose_line("   "))
        self.assertFalse(is_prose_line(""))


if __name__ == "__main__":
    unittest.main()
