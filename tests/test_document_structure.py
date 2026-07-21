import unittest

from calamus_document_structure import (
    DocumentHeading,
    DocumentStructure,
    build_document_structure,
)


class DocumentStructureParserTests(unittest.TestCase):
    def test_empty_and_plain_text_have_no_headings(self):
        self.assertEqual(build_document_structure("").headings, ())
        self.assertEqual(build_document_structure("plain\ntext").headings, ())

    def test_atx_headings_support_levels_titles_lines_and_offsets(self):
        text = "# Title\ntext\n  ## Section ##  \nbody\n###### Final\n"
        structure = build_document_structure(text)
        self.assertEqual(
            [(item.level, item.title, item.line, item.start_offset) for item in structure.headings],
            [
                (1, "Title", 1, 0),
                (2, "Section", 3, text.index("  ## Section")),
                (6, "Final", 5, text.index("###### Final")),
            ],
        )

    def test_heading_requires_whitespace_after_hash_run(self):
        text = "#validly-not-a-heading\n# Valid\n"
        structure = build_document_structure(text)
        self.assertEqual([item.title for item in structure.headings], ["Valid"])
        self.assertEqual(structure.headings[0].line, 2)

    def test_headings_inside_backtick_and_tilde_fences_are_ignored(self):
        text = (
            "# Visible\n"
            "```markdown\n"
            "## Hidden\n"
            "```\n"
            "~~~\n"
            "### Hidden too\n"
            "~~~~\n"
            "## Visible again\n"
        )
        structure = build_document_structure(text)
        self.assertEqual(
            [(item.level, item.title) for item in structure.headings],
            [(1, "Visible"), (2, "Visible again")],
        )

    def test_duplicate_titles_keep_distinct_exact_offsets(self):
        text = "# Same\nA\n# Same\nB\n"
        first, second = build_document_structure(text).headings
        self.assertEqual(first.title, second.title)
        self.assertNotEqual(first.start_offset, second.start_offset)
        self.assertEqual(second.start_offset, text.index("# Same", 1))

    def test_section_end_tracks_next_same_or_higher_level_heading(self):
        text = "# One\nA\n## Child\nB\n### Grandchild\nC\n# Two\nD\n"
        one, child, grandchild, two = build_document_structure(text).headings
        second_top = text.index("# Two")
        self.assertEqual(one.section_end_offset, second_top)
        self.assertEqual(child.section_end_offset, second_top)
        self.assertEqual(grandchild.section_end_offset, second_top)
        self.assertEqual(two.section_end_offset, len(text))

    def test_parser_handles_crlf_and_unicode_line_separator_offsets(self):
        text = "# One\r\nbody\u2028## Two\rfinal"
        structure = build_document_structure(text)
        self.assertEqual([item.line for item in structure.headings], [1, 3])
        self.assertEqual(structure.headings[1].start_offset, text.index("## Two"))

    def test_empty_heading_is_preserved_with_display_fallback(self):
        heading = build_document_structure("###\n").headings[0]
        self.assertEqual(heading.title, "")
        self.assertEqual(heading.display_title, "(Untitled heading)")

    def test_parser_rejects_non_string_input(self):
        with self.assertRaises(TypeError):
            build_document_structure(None)


class DocumentStructureNavigationTests(unittest.TestCase):
    def setUp(self):
        self.text = "preface\n# One\nA\n## Child\nB\n# Two\nC\n"
        self.structure = build_document_structure(self.text)
        self.one, self.child, self.two = self.structure.headings

    def test_current_heading_is_last_heading_at_or_before_cursor(self):
        self.assertIsNone(self.structure.current_heading(0))
        self.assertEqual(self.structure.current_heading(self.one.start_offset), self.one)
        self.assertEqual(self.structure.current_heading(self.child.start_offset + 2), self.child)
        self.assertEqual(self.structure.current_heading(len(self.text)), self.two)

    def test_next_heading_does_not_wrap(self):
        self.assertEqual(self.structure.next_heading(0), self.one)
        self.assertEqual(self.structure.next_heading(self.one.start_offset), self.child)
        self.assertIsNone(self.structure.next_heading(len(self.text)))

    def test_previous_heading_does_not_wrap(self):
        self.assertIsNone(self.structure.previous_heading(0))
        self.assertIsNone(self.structure.previous_heading(self.one.start_offset))
        self.assertEqual(self.structure.previous_heading(self.child.start_offset), self.one)
        self.assertEqual(self.structure.previous_heading(len(self.text)), self.two)

    def test_filter_is_case_insensitive_and_preserves_document_order(self):
        self.assertEqual(self.structure.filtered("o"), (self.one, self.two))
        self.assertEqual(self.structure.filtered("CHILD"), (self.child,))
        self.assertEqual(self.structure.filtered(""), self.structure.headings)

    def test_offset_validation(self):
        with self.assertRaises(TypeError):
            self.structure.current_heading(True)
        with self.assertRaises(ValueError):
            self.structure.next_heading(-1)
        with self.assertRaises(TypeError):
            self.structure.filtered(None)

    def test_model_validation(self):
        with self.assertRaises(ValueError):
            DocumentHeading(0, "bad", 1, 0, 0)
        with self.assertRaises(ValueError):
            DocumentHeading(1, "bad", 0, 0, 0)
        with self.assertRaises(ValueError):
            DocumentHeading(1, "bad", 1, 5, 4)
        with self.assertRaises(ValueError):
            DocumentStructure((DocumentHeading(1, "bad", 1, 2, 4),), 3)


if __name__ == "__main__":
    unittest.main()
