import os
import tempfile
import unittest

import calamus_writing as w
import calamus_clips as clips


class WritingToolsTests(unittest.TestCase):
    def test_sort_lines_preserves_final_newline(self):
        self.assertEqual(w.sort_lines("b\na\n"), "a\nb\n")
        self.assertEqual(w.sort_lines("a\nb", reverse=True), "b\na")

    def test_clean_pdf_text_removes_hyphenation_and_keeps_paragraphs(self):
        src = "Questo è un testo spez-\nzato da PDF\ncon righe rotte.\n\nNuovo paragrafo."
        self.assertEqual(w.clean_pdf_text(src), "Questo è un testo spezzato da PDF con righe rotte.\n\nNuovo paragrafo.")

    def test_reflow_and_join_lines(self):
        src = "una riga\nspezzata\n\naltra"
        self.assertEqual(w.join_lines(src), "una riga spezzata\n\naltra")
        self.assertIn("una riga spezzata", w.reflow_paragraph(src, width=80))

    def test_cleanup_spaces(self):
        self.assertEqual(w.remove_extra_spaces(" a   b \n c\t d "), "a b\nc d")
        self.assertEqual(w.remove_trailing_spaces("a  \nb\t\n"), "a\nb\n")

    def test_smart_typography_and_case_tools(self):
        self.assertEqual(w.smart_typography('"ciao" -- ok...'), '“ciao” — ok…')
        self.assertEqual(w.title_case("ciao MONDO"), "Ciao Mondo")
        self.assertEqual(w.sentence_case("CIAO. MONDO"), "Ciao. Mondo")

    def test_document_statistics(self):
        stats = w.document_statistics("uno due\n\ntre")
        self.assertEqual(stats["words"], 3)
        self.assertEqual(stats["paragraphs"], 2)

    def test_templates(self):
        with tempfile.TemporaryDirectory() as td:
            items = w.list_templates(td)
            self.assertTrue(any(name == "blank-note.txt" for name, _ in items))
            name, path = items[0]
            self.assertIsInstance(w.read_template(path), str)

    def test_clips_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            item = clips.new_clip("Greeting", "Hello")
            self.assertTrue(clips.save_clips(td, [item]))
            loaded = clips.load_clips(td)
            self.assertEqual(loaded[0]["title"], "Greeting")
            self.assertEqual(loaded[0]["text"], "Hello")


if __name__ == "__main__":
    unittest.main()

class WritingRegressionExtraTests(unittest.TestCase):
    def test_clean_pdf_preserves_multiple_paragraphs(self):
        src = "Prima riga\ncontinua.\n\nSecondo para-\ngrafo\nancora.\n\nTerzo."
        self.assertEqual(w.clean_pdf_text(src), "Prima riga continua.\n\nSecondo paragrafo ancora.\n\nTerzo.")

    def test_reflow_respects_width_reasonably(self):
        out = w.reflow_paragraph("uno due tre quattro cinque", width=10)
        self.assertIn("\n", out)
        self.assertIn("quattro", out)

    def test_document_statistics_empty_text(self):
        stats = w.document_statistics("")
        self.assertEqual(stats["words"], 0)
        self.assertEqual(stats["characters"], 0)
