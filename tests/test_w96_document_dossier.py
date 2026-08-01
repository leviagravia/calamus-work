from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from calamus_document_dossier import (
    DocumentDossierInputs,
    build_document_dossier,
    document_dossier_authority_stamp,
)
from calamus_document_dossier_controller import DocumentDossierController
from calamus_reference_set_store import ReferenceSetSnapshot
from calamus_reference_sets import ReferenceSet
from calamus_reference_store import ReferenceLibrarySnapshot
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken
from calamus_source_note_store import SourceNoteSnapshot
from calamus_source_notes import SourceLocator, SourceNote


TOKEN_A = FileToken(True, 1, 10, "a" * 64)
TOKEN_B = FileToken(True, 2, 20, "b" * 64)
TOKEN_C = FileToken(True, 3, 30, "c" * 64)
TOKEN_D = FileToken(True, 4, 40, "d" * 64)


def record(key, title, *, aliases=(), related=()):
    extra = (("Related Keys", ", ".join(related)),) if related else ()
    return ReferenceRecord(
        key=key,
        title=title,
        authors=(f"Author {key}",),
        year="2026",
        aliases=aliases,
        extra_fields=extra,
    )


def note(note_id, kind, text, *, reference_key="", target="", locator=None):
    return SourceNote(
        id=note_id,
        kind=kind,
        text=text,
        reference_key=reference_key,
        target=target,
        locator=locator or SourceLocator(),
    )


def inputs(
    text,
    *,
    path="/tmp/article.md",
    modified=False,
    records=(),
    notes=(),
    sets=(),
    bookmarks=(),
):
    return DocumentDossierInputs(
        document_text=text,
        document_path=path,
        modified=modified,
        bookmarks=bookmarks,
        reference_snapshot=ReferenceLibrarySnapshot(tuple(records), TOKEN_B, ()),
        source_note_snapshot=SourceNoteSnapshot(tuple(notes), TOKEN_C, ()),
        reference_set_snapshot=ReferenceSetSnapshot(tuple(sets), TOKEN_D, ()),
        document_token=TOKEN_A,
        refreshed_at="2026-07-31T21:30:00+02:00",
    )


class DocumentDossierCoreTests(unittest.TestCase):
    def test_empty_untitled_document_degrades_without_sidecar(self):
        snapshot = build_document_dossier(DocumentDossierInputs(""))
        self.assertEqual("Untitled", snapshot.identity.name)
        self.assertTrue(snapshot.identity.untitled)
        self.assertFalse(snapshot.capabilities.can_use_source_notes)
        self.assertEqual(0, snapshot.statistics.words)
        self.assertEqual(0, snapshot.counts.sections)
        self.assertEqual((), snapshot.references)

    def test_identity_uses_current_path_and_modified_state(self):
        snapshot = build_document_dossier(inputs("Text", path="/tmp/My Essay.md", modified=True))
        self.assertEqual("My Essay.md", snapshot.identity.name)
        self.assertEqual("/tmp/My Essay.md", snapshot.identity.path)
        self.assertTrue(snapshot.identity.modified)
        self.assertFalse(snapshot.identity.untitled)
        self.assertTrue(snapshot.capabilities.can_use_source_notes)

    def test_structure_citations_notes_and_statistics_are_derived(self):
        text = "# Intro {#intro}\nAlpha [@alpha, p. 3].\n\n## Method {#method}\nBeta.\n"
        alpha = record("alpha", "Alpha Book")
        source_note = note(
            "note-1",
            "quote",
            "A source excerpt",
            reference_key="alpha",
            target="method",
            locator=SourceLocator(page="3"),
        )
        snapshot = build_document_dossier(inputs(text, records=(alpha,), notes=(source_note,)))
        self.assertEqual(2, snapshot.counts.sections)
        self.assertEqual(1, snapshot.counts.citations)
        self.assertEqual(1, snapshot.counts.source_notes)
        self.assertEqual("intro", snapshot.sections[0].id)
        self.assertEqual("method", snapshot.sections[1].id)
        self.assertEqual(1, snapshot.sections[0].citation_count)
        self.assertEqual(1, snapshot.sections[1].source_note_count)
        self.assertGreater(snapshot.statistics.words, 0)
        self.assertEqual("complete", snapshot.source_notes[0].status)

    def test_related_references_and_pertinent_sets_are_in_core(self):
        text = "# Topic {#topic}\nSee [@alpha].\n"
        alpha = record("alpha", "Alpha", related=("beta",))
        beta = record("beta", "Beta")
        gamma = record("gamma", "Gamma")
        unrelated = record("unrelated", "Unrelated")
        sets = (
            ReferenceSet("Topic Set", "Relevant sources", ("beta", "gamma")),
            ReferenceSet("Other Set", "Irrelevant", ("unrelated",)),
        )
        snapshot = build_document_dossier(
            inputs(text, records=(alpha, beta, gamma, unrelated), sets=sets)
        )
        by_key = {item.key: item for item in snapshot.references}
        self.assertEqual({"alpha", "beta", "gamma"}, set(by_key))
        self.assertIn("cited", by_key["alpha"].roles)
        self.assertIn("related", by_key["beta"].roles)
        self.assertIn("reference-set", by_key["beta"].roles)
        self.assertIn("reference-set", by_key["gamma"].roles)
        self.assertIn("collected-unused", by_key["beta"].roles)
        self.assertIn("collected-unused", by_key["gamma"].roles)
        self.assertEqual(("alpha",), by_key["beta"].related_from)
        self.assertEqual(("Topic Set",), by_key["gamma"].reference_sets)
        self.assertEqual(("Topic Set",), tuple(item.name for item in snapshot.reference_sets))
        self.assertEqual(1, snapshot.counts.related_references)
        self.assertEqual(2, snapshot.counts.collected_unused_references)
        self.assertEqual(1, snapshot.counts.relevant_reference_sets)

    def test_incoming_legacy_related_relation_is_visible_symmetrically(self):
        alpha = record("alpha", "Alpha")
        beta = record("beta", "Beta", related=("alpha",))
        snapshot = build_document_dossier(
            inputs("[@alpha]", records=(alpha, beta))
        )
        beta_view = snapshot.reference("beta")
        self.assertIsNotNone(beta_view)
        assert beta_view is not None
        self.assertIn("related", beta_view.roles)
        self.assertEqual(("alpha",), beta_view.related_from)

    def test_unrelated_global_library_records_and_unused_advisories_are_excluded(self):
        alpha = record("alpha", "Alpha")
        unused = record("unused", "Unused")
        snapshot = build_document_dossier(
            inputs("[@alpha]", records=(alpha, unused))
        )
        self.assertIsNone(snapshot.reference("unused"))
        self.assertFalse(
            any(issue.kind == "reference-unused" and issue.subject == "unused" for issue in snapshot.issues)
        )

    def test_missing_and_ambiguous_reference_identities_are_visible(self):
        one = record("one", "One", aliases=("shared",))
        two = record("two", "Two", aliases=("shared",))
        snapshot = build_document_dossier(
            inputs("[@missing; @shared]", records=(one, two))
        )
        missing = snapshot.reference("missing")
        shared = snapshot.reference("shared")
        self.assertEqual("missing", missing.status)
        self.assertEqual("ambiguous", shared.status)
        self.assertIn("missing", missing.roles)
        self.assertEqual(("missing",), snapshot.citations[0].missing_keys)
        self.assertEqual(("shared",), snapshot.citations[0].ambiguous_keys)

    def test_reference_alias_resolves_to_canonical_key(self):
        alpha = record("alpha", "Alpha", aliases=("old-alpha",))
        snapshot = build_document_dossier(inputs("[@old-alpha]", records=(alpha,)))
        self.assertEqual(("alpha",), snapshot.citations[0].canonical_keys)
        self.assertEqual("alpha", snapshot.references[0].key)
        self.assertEqual(1, snapshot.references[0].cited_count)

    def test_citation_item_multiplicity_is_preserved_for_exact_counts(self):
        alpha = record("alpha", "Alpha")
        snapshot = build_document_dossier(inputs("[@alpha; @alpha]", records=(alpha,)))
        self.assertEqual(("alpha", "alpha"), snapshot.citations[0].requested_keys)
        self.assertEqual(("alpha", "alpha"), snapshot.citations[0].canonical_keys)
        self.assertEqual(2, snapshot.counts.citations)
        self.assertEqual(2, snapshot.reference("alpha").cited_count)

    def test_reference_set_is_relevant_through_related_reference(self):
        alpha = record("alpha", "Alpha", related=("beta",))
        beta = record("beta", "Beta")
        gamma = record("gamma", "Gamma")
        item = ReferenceSet("Extended", "", ("beta", "gamma"))
        snapshot = build_document_dossier(
            inputs("[@alpha]", records=(alpha, beta, gamma), sets=(item,))
        )
        self.assertEqual(("Extended",), tuple(value.name for value in snapshot.reference_sets))
        self.assertIn("reference-set", snapshot.reference("gamma").roles)

    def test_reference_set_missing_member_is_preserved_without_fabricated_record(self):
        alpha = record("alpha", "Alpha")
        item = ReferenceSet("Set", "", ("alpha", "not-there"))
        snapshot = build_document_dossier(
            inputs("[@alpha]", records=(alpha,), sets=(item,))
        )
        self.assertEqual(("not-there",), snapshot.reference_sets[0].missing_members)
        self.assertIsNone(snapshot.reference("not-there"))
        self.assertTrue(any(issue.kind == "reference-set-member-missing" for issue in snapshot.issues))

    def test_links_are_resolved_missing_or_ambiguous(self):
        text = (
            "# One {#one}\n[Go](#two) [Missing](#missing)\n"
            "# Two {#two}\nText\n"
            "# Duplicate {#dup}\n# Duplicate Again {#dup}\n[Dup](#dup)\n"
        )
        snapshot = build_document_dossier(inputs(text))
        statuses = {item.identifier: item.status for item in snapshot.links}
        self.assertEqual("resolved", statuses["two"])
        self.assertEqual("missing", statuses["missing"])
        self.assertEqual("ambiguous", statuses["dup"])
        resolved = next(item for item in snapshot.links if item.identifier == "two")
        self.assertEqual("two", resolved.destination_section_id)
        self.assertEqual(3, resolved.destination_line)

    def test_bookmarks_are_mapped_to_lines_and_sections(self):
        text = "# One {#one}\nFirst\n# Two {#two}\nSecond\n"
        second_offset = text.index("Second")
        snapshot = build_document_dossier(inputs(text, bookmarks=(0, second_offset)))
        self.assertEqual(2, snapshot.counts.bookmarks)
        self.assertEqual("one", snapshot.bookmarks[0].section_id)
        self.assertEqual("two", snapshot.bookmarks[1].section_id)
        self.assertEqual(1, snapshot.sections[0].bookmark_count)
        self.assertEqual(1, snapshot.sections[1].bookmark_count)

    def test_source_note_statuses_cover_complete_incomplete_and_orphan(self):
        alpha = record("alpha", "Alpha")
        notes = (
            note("complete", "quote", "Complete", reference_key="alpha", target="one", locator=SourceLocator(page="1")),
            note("incomplete", "quote", "No locator", reference_key="alpha", target="one"),
            note("orphan", "comment", "Missing target", target="absent"),
        )
        snapshot = build_document_dossier(
            inputs("# One {#one}\nText\n", records=(alpha,), notes=notes)
        )
        statuses = {item.id: item.status for item in snapshot.source_notes}
        self.assertEqual("complete", statuses["complete"])
        self.assertEqual("incomplete", statuses["incomplete"])
        self.assertEqual("orphan", statuses["orphan"])

    def test_section_local_counts_include_links_citations_notes_and_bookmarks(self):
        text = "# One {#one}\n[@alpha] [Two](#two)\n# Two {#two}\nText\n"
        alpha = record("alpha", "Alpha")
        source_note = note("n1", "comment", "Comment", target="two")
        snapshot = build_document_dossier(
            inputs(text, records=(alpha,), notes=(source_note,), bookmarks=(text.index("Text"),))
        )
        one = snapshot.section("one")
        two = snapshot.section("two")
        self.assertEqual(1, one.citation_count)
        self.assertEqual(1, one.outgoing_link_count)
        self.assertEqual(1, two.incoming_link_count)
        self.assertEqual(1, two.source_note_count)
        self.assertEqual(1, two.bookmark_count)

    def test_authority_stamp_contains_live_buffer_and_all_tokens(self):
        value = inputs("Alpha", modified=True)
        stamp = document_dossier_authority_stamp(value)
        self.assertEqual("/tmp/article.md", stamp.document_path)
        self.assertTrue(stamp.modified)
        self.assertEqual(64, len(stamp.buffer_digest))
        self.assertEqual(TOKEN_A, stamp.document_token)
        self.assertEqual(TOKEN_B, stamp.references_token)
        self.assertEqual(TOKEN_C, stamp.source_notes_token)
        self.assertEqual(TOKEN_D, stamp.reference_sets_token)
        self.assertNotEqual(stamp, document_dossier_authority_stamp(replace(value, document_text="Beta")))

    def test_inputs_clamp_and_deduplicate_bookmarks(self):
        value = DocumentDossierInputs("abc", bookmarks=(3, 99, 3, 0))
        self.assertEqual((0, 3), value.bookmarks)

    def test_controller_refreshes_only_when_stale_or_authorities_change(self):
        state = {"inputs": inputs("Alpha")}
        controller = DocumentDossierController(lambda: state["inputs"])
        first = controller.ensure_current()
        self.assertEqual(1, controller.refresh_count)
        self.assertIs(first, controller.ensure_current())
        self.assertEqual(1, controller.refresh_count)
        state["inputs"] = replace(state["inputs"], document_text="Beta")
        second = controller.ensure_current()
        self.assertEqual(2, controller.refresh_count)
        self.assertNotEqual(first.authority_stamp, second.authority_stamp)
        controller.mark_stale()
        controller.ensure_current()
        self.assertEqual(3, controller.refresh_count)

    def test_controller_rejects_invalid_provider_result(self):
        controller = DocumentDossierController(lambda: "not inputs")
        with self.assertRaises(TypeError):
            controller.refresh()

    def test_model_and_controller_are_gtk_free(self):
        import calamus_document_dossier
        import calamus_document_dossier_controller

        source = inspect.getsource(calamus_document_dossier) + inspect.getsource(calamus_document_dossier_controller)
        for token in ("import gi", "from gi", "Gtk.", "Gdk.", "Gio."):
            self.assertNotIn(token, source)

    def test_long_document_build_is_deterministic(self):
        sections = [f"# Section {index} {{#s{index}}}\nText [@alpha].\n" for index in range(1, 401)]
        text = "\n".join(sections)
        alpha = record("alpha", "Alpha")
        first = build_document_dossier(inputs(text, records=(alpha,)))
        second = build_document_dossier(inputs(text, records=(alpha,)))
        self.assertEqual(first, second)
        self.assertEqual(400, first.counts.sections)
        self.assertEqual(400, first.counts.citations)
        self.assertEqual(400, first.reference("alpha").cited_count)


if __name__ == "__main__":
    unittest.main()
