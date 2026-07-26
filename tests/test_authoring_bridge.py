import unittest

from calamus_authoring_bridge import (
    EditorSelectionSnapshot,
    build_authoring_bridge_projection,
    format_heading_link,
    parse_markdown_heading_links,
    plan_heading_link_insertion,
    unique_heading_identifier_at_offset,
)
from calamus_document_structure import build_document_structure
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceNote


class AuthoringBridgeModelTests(unittest.TestCase):
    def setUp(self):
        self.text = (
            "# Introduction {#intro}\n"
            "See [the method](#method) and [missing](#missing).\n"
            "Cite [@oldkey, p. 3; @missingref].\n"
            "Inline `[ignored](#intro)` stays code.\n"
            "```md\n[also ignored](#method) [@oldkey]\n```\n"
            "## Method {#method}\n"
            "Body.\n"
        )
        self.structure = build_document_structure(self.text)
        self.records = (
            ReferenceRecord(
                key="canonical",
                aliases=("oldkey",),
                title="A Study",
                authors=("Doe, Jane",),
                year="2024",
            ),
        )
        self.notes = (
            SourceNote(
                id="sn-one",
                kind="quote",
                text="A linked quotation",
                reference_key="oldkey",
                target="#intro",
            ),
            SourceNote(
                id="sn-broken-ref",
                kind="quote",
                text="Broken source",
                reference_key="lost",
            ),
            SourceNote(
                id="sn-broken-target",
                kind="comment",
                text="Broken target",
                target="#lost-heading",
            ),
        )

    def test_heading_link_parser_excludes_fenced_and_inline_code(self):
        links = parse_markdown_heading_links(self.text)
        self.assertEqual(
            [(item.label, item.identifier) for item in links],
            [("the method", "method"), ("missing", "missing")],
        )
        self.assertEqual(links[0].line, 2)
        self.assertEqual(self.text[links[0].start_offset:links[0].end_offset], "[the method](#method)")

    def test_projection_derives_reference_and_heading_backlinks_and_issues(self):
        projection = build_authoring_bridge_projection(
            self.records,
            self.text,
            self.notes,
            self.structure,
        )
        self.assertEqual([item.identifier for item in projection.reference_subjects], ["canonical"])
        self.assertEqual([item.identifier for item in projection.heading_subjects], ["intro", "method"])

        reference_items = projection.items("reference", "canonical")
        self.assertEqual(
            [item.kind for item in reference_items],
            ["citation", "source-note-reference"],
        )
        citation = reference_items[0]
        self.assertEqual(citation.navigation_kind, "document")
        self.assertEqual(self.text[citation.start_offset:citation.end_offset], "[@oldkey, p. 3; @missingref]")
        self.assertEqual(reference_items[1].source_note_id, "sn-one")

        intro_items = projection.items("heading", "intro")
        self.assertEqual([item.kind for item in intro_items], ["source-note-target"])
        method_items = projection.items("heading", "method")
        self.assertEqual([item.kind for item in method_items], ["heading-link"])

        issues = projection.items("issues", "broken-links")
        self.assertEqual(
            {item.kind for item in issues},
            {
                "broken-citation",
                "broken-heading-link",
                "broken-source-note-reference",
                "broken-source-note-target",
            },
        )
        self.assertEqual(len({item.id for item in projection.occurrences}), len(projection.occurrences))

    def test_projection_is_deterministic_and_unicode_safe(self):
        text = "# Théologie {#theologie}\nVedi [Théologie](#theologie) [@ref].\n"
        records = (ReferenceRecord(key="ref", title="Église", authors=("Daniélou, Jean",)),)
        structure = build_document_structure(text)
        first = build_authoring_bridge_projection(records, text, (), structure)
        second = build_authoring_bridge_projection(records, text, (), structure)
        self.assertEqual(first, second)
        self.assertIn("Théologie", first.items("heading", "theologie")[0].label)

    def test_duplicate_heading_identifier_is_not_a_subject_and_is_reported(self):
        text = "# One {#same}\n[go](#same)\n## Two {#same}\n"
        projection = build_authoring_bridge_projection((), text, (), build_document_structure(text))
        self.assertEqual(projection.heading_subjects, ())
        kinds = [item.kind for item in projection.items("issues", "broken-links")]
        self.assertIn("broken-heading-link", kinds)
        self.assertIn("heading-diagnostic", kinds)

    def test_projection_rejects_structure_from_another_snapshot(self):
        with self.assertRaisesRegex(ValueError, "does not belong"):
            build_authoring_bridge_projection((), "different", (), self.structure)

    def test_unique_heading_identifier_uses_selection_offset_and_fails_closed(self):
        selected = self.text.index("See [the method]")
        self.assertEqual(
            unique_heading_identifier_at_offset(self.structure, selected),
            "intro",
        )
        before_heading = build_document_structure("Preface\n# Start {#start}\n")
        self.assertIsNone(unique_heading_identifier_at_offset(before_heading, 0))
        duplicate = build_document_structure(
            "# One {#same}\nText\n## Two {#same}\nMore\n"
        )
        self.assertIsNone(
            unique_heading_identifier_at_offset(duplicate, duplicate.text_length)
        )


class EditorSelectionSnapshotTests(unittest.TestCase):
    def test_snapshot_owns_exact_text_and_offsets(self):
        snapshot = EditorSelectionSnapshot("alpha beta", 6, 10)
        self.assertTrue(snapshot.has_selection)
        self.assertEqual(snapshot.selected_text, "beta")

    def test_cursor_snapshot_and_invalid_ranges(self):
        snapshot = EditorSelectionSnapshot("text", 2, 2)
        self.assertFalse(snapshot.has_selection)
        self.assertEqual(snapshot.selected_text, "")
        with self.assertRaisesRegex(ValueError, "range"):
            EditorSelectionSnapshot("text", 3, 2)
        with self.assertRaisesRegex(ValueError, "range"):
            EditorSelectionSnapshot("text", 0, 5)
        with self.assertRaises(TypeError):
            EditorSelectionSnapshot("text", True, 1)


class HeadingLinkPlannerTests(unittest.TestCase):
    def setUp(self):
        self.text = "# Start {#start}\nText here.\n## Method {#method}\n"
        self.structure = build_document_structure(self.text)

    def test_insert_at_cursor(self):
        cursor = self.text.index("Text")
        plan = plan_heading_link_insertion(
            self.text,
            cursor,
            cursor,
            "method",
            "Method",
            self.structure,
        )
        self.assertTrue(plan.changed)
        self.assertEqual(plan.replacement, "[Method](#method)")
        self.assertEqual(
            plan.document_after,
            self.text[:cursor] + "[Method](#method)" + self.text[cursor:],
        )
        self.assertEqual(plan.cursor_after, cursor + len(plan.replacement))

    def test_replace_selection_and_escape_label(self):
        start = self.text.index("Text")
        end = start + len("Text")
        plan = plan_heading_link_insertion(
            self.text,
            start,
            end,
            "#method",
            "See ] method",
            self.structure,
        )
        self.assertEqual(plan.replacement, r"[See \] method](#method)")
        self.assertEqual(plan.document_after[start:start + len(plan.replacement)], plan.replacement)

    def test_empty_multiline_missing_ambiguous_and_stale_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            format_heading_link(" ", "method")
        with self.assertRaisesRegex(ValueError, "one line"):
            format_heading_link("one\ntwo", "method")
        with self.assertRaisesRegex(ValueError, "missing"):
            plan_heading_link_insertion(
                self.text, 0, 0, "lost", "Lost", self.structure
            )
        duplicate = "# A {#same}\n## B {#same}\n"
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            plan_heading_link_insertion(
                duplicate,
                0,
                0,
                "same",
                "Same",
                build_document_structure(duplicate),
            )
        with self.assertRaisesRegex(ValueError, "changed"):
            plan_heading_link_insertion(
                self.text + "x", 0, 0, "method", "Method", self.structure
            )


if __name__ == "__main__":
    unittest.main()
