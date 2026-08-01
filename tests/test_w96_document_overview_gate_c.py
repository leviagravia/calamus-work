from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest

from calamus_document_dossier import DocumentDossierInputs
from calamus_document_dossier_app import build_document_dossier_inputs
from calamus_document_dossier_controller import DocumentDossierController
from calamus_document_overview_runtime import DocumentOverviewRuntime
from calamus_reference_set_store import MarkdownReferenceSetStore, ReferenceSetSnapshot
from calamus_reference_sets import ReferenceSet
from calamus_reference_store import MarkdownReferenceStore, ReferenceLibrarySnapshot
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken
from calamus_source_note_store import MarkdownSourceNoteStore, SourceNoteSnapshot, source_notes_path
from calamus_source_notes import SourceLocator, SourceNote


class FakeWindow:
    def __init__(self):
        self.callbacks = {}
        self.destroyed = False

    def connect(self, signal, callback):
        self.callbacks[signal] = callback

    def destroy(self):
        if self.destroyed:
            return
        self.destroyed = True
        callback = self.callbacks.get("destroy")
        if callback:
            callback(self)


class FakeView:
    def __init__(self):
        self.window = FakeWindow()
        self.callbacks = {}
        self.categories = []
        self.items = []
        self.details = []
        self.headers = []
        self.present_count = 0
        self.stale = False

    def bind(self, **callbacks): self.callbacks = callbacks
    def render_header(self, **values): self.headers.append(values)
    def render_categories(self, selected, counts): self.categories.append((selected, counts))
    def render_items(self, heading, rows, selected): self.items.append((heading, rows, selected))
    def render_detail(self, **values): self.details.append(values)
    def set_stale(self, stale): self.stale = bool(stale)
    def present(self): self.present_count += 1
    def destroy(self): self.window.destroy()


def token(marker: str, mtime: int = 1) -> FileToken:
    return FileToken(True, mtime, 10, marker * 64)


def record(key: str, title: str, *, related=()) -> ReferenceRecord:
    extra = (("Related Keys", ", ".join(related)),) if related else ()
    return ReferenceRecord(key=key, title=title, extra_fields=extra)


def note(note_id: str, key: str = "alpha", target: str = "intro") -> SourceNote:
    return SourceNote(
        id=note_id,
        kind="quote",
        text="Quoted text",
        reference_key=key,
        target=target,
        locator=SourceLocator(page="12"),
    )


def make_inputs(
    text: str = "# Intro {#intro}\nText [@alpha].\n",
    *,
    records=(None,),
    notes=(None,),
    sets=(None,),
    ref_token=None,
    note_token=None,
    set_token=None,
) -> DocumentDossierInputs:
    actual_records = (record("alpha", "Alpha"),) if records == (None,) else tuple(records)
    actual_notes = (note("note-1"),) if notes == (None,) else tuple(notes)
    actual_sets = (ReferenceSet("Core", members=("alpha",)),) if sets == (None,) else tuple(sets)
    return DocumentDossierInputs(
        text,
        document_path="/tmp/article.md",
        modified=True,
        reference_snapshot=ReferenceLibrarySnapshot(actual_records, ref_token or token("a"), ()),
        source_note_snapshot=SourceNoteSnapshot(actual_notes, note_token or token("b"), ()),
        reference_set_snapshot=ReferenceSetSnapshot(actual_sets, set_token or token("c"), ()),
        document_token=token("d"),
        refreshed_at="2026-07-31T22:00:00+02:00",
    )


class GateCRuntimeTests(unittest.TestCase):
    def make_runtime(self, initial=None):
        state = {"inputs": initial or make_inputs()}
        controller = DocumentDossierController(lambda: state["inputs"])
        calls = []
        views = []

        def factory(_parent):
            view = FakeView()
            views.append(view)
            return view

        runtime = DocumentOverviewRuntime(
            object(),
            controller,
            navigate_offset=lambda value: calls.append(("offset", value)) or True,
            select_range=lambda start, end: calls.append(("range", start, end)) or True,
            show_reference=lambda key: calls.append(("reference", key)) or True,
            show_source_note=lambda key: calls.append(("note", key)) or True,
            show_reference_set=lambda name: calls.append(("set", name)) or True,
            run_research_check=lambda: calls.append(("check",)) or True,
            focus_document=lambda: calls.append(("focus",)) or True,
            show_error=lambda message: calls.append(("error", message)),
            show_notice=lambda message: calls.append(("notice", message)),
            view_factory=factory,
        )
        return runtime, controller, state, calls, views

    def select_kind(self, runtime, views, category, kind):
        runtime.select_category(category)
        row = next(item for item in views[-1].items[-1][1] if item.kind == kind)
        runtime.select_item(row.id)
        return row

    def assert_stale_action_blocked(self, runtime, controller, calls, before_refresh):
        self.assertFalse(runtime.activate_primary())
        self.assertEqual(before_refresh + 1, controller.refresh_count)
        self.assertFalse(any(call[0] in {"offset", "range", "reference", "note", "set", "check"} for call in calls))
        self.assertTrue(any(call[0] == "notice" and "Select the item again" in call[1] for call in calls))
        self.assertIsNone(runtime._selected_item_id)

    def test_changed_document_after_heading_selection_refreshes_and_blocks(self):
        runtime, controller, state, calls, views = self.make_runtime()
        runtime.open()
        self.select_kind(runtime, views, "structure", "section")
        before = controller.refresh_count
        state["inputs"] = replace(state["inputs"], document_text="# Renamed {#renamed}\nDifferent\n")
        self.assert_stale_action_blocked(runtime, controller, calls, before)

    def test_removed_citation_after_selection_refreshes_and_blocks(self):
        runtime, controller, state, calls, views = self.make_runtime()
        runtime.open()
        self.select_kind(runtime, views, "research", "citation")
        before = controller.refresh_count
        state["inputs"] = replace(state["inputs"], document_text="# Intro {#intro}\nNo citation.\n")
        self.assert_stale_action_blocked(runtime, controller, calls, before)

    def test_removed_source_note_reference_and_set_each_fail_closed(self):
        for kind, update in (
            ("source-note", {"notes": (), "note_token": token("e", 2)}),
            ("reference", {"records": (), "ref_token": token("f", 2)}),
            ("reference-set", {"sets": (), "set_token": token("g", 2)}),
        ):
            with self.subTest(kind=kind):
                runtime, controller, state, calls, views = self.make_runtime()
                runtime.open()
                self.select_kind(runtime, views, "research", kind)
                before = controller.refresh_count
                state["inputs"] = make_inputs(**update)
                self.assert_stale_action_blocked(runtime, controller, calls, before)

    def test_valid_current_action_re_resolves_and_delegates_once(self):
        runtime, controller, _state, calls, views = self.make_runtime()
        runtime.open()
        row = self.select_kind(runtime, views, "research", "reference")
        self.assertTrue(runtime.activate_primary())
        self.assertEqual(("reference", row.payload.key), calls[-1])
        self.assertEqual(1, controller.refresh_count)

    def test_callback_failure_is_contained_and_reported(self):
        runtime, _controller, _state, calls, views = self.make_runtime()
        runtime._show_reference = lambda _key: (_ for _ in ()).throw(RuntimeError("boom"))
        runtime.open()
        self.select_kind(runtime, views, "research", "reference")
        self.assertFalse(runtime.activate_primary())
        self.assertTrue(any(call[0] == "error" and "boom" in call[1] for call in calls))

    def test_repeated_open_refresh_close_releases_window_rows_and_snapshot(self):
        runtime, controller, _state, calls, views = self.make_runtime()
        for cycle in range(12):
            self.assertTrue(runtime.open())
            self.assertTrue(runtime.refresh())
            self.assertTrue(runtime.close())
            self.assertFalse(runtime.is_open)
            self.assertIsNone(runtime.snapshot)
            self.assertEqual((), runtime._rows)
            self.assertIsNone(runtime._selected_item_id)
            self.assertTrue(views[cycle].window.destroyed)
        self.assertEqual(24, controller.refresh_count)
        self.assertEqual(12, calls.count(("focus",)))


class GateCHostileModelTests(unittest.TestCase):
    def test_long_document_and_high_item_counts_are_iterative_and_exact(self):
        parts = []
        records = []
        for index in range(1, 751):
            key = f"ref{index}"
            parts.append(f"## Section {index} {{#section-{index}}}\nText [@{key}].\n")
            records.append(record(key, f"Reference {index}"))
        snapshot = DocumentDossierController(
            lambda: make_inputs("\n".join(parts), records=tuple(records), notes=(), sets=())
        ).refresh()
        self.assertEqual(750, len(snapshot.sections))
        self.assertEqual(750, snapshot.counts.citations)
        self.assertEqual(750, len(snapshot.references))
        self.assertEqual("section-750", snapshot.sections[-1].id)

    def test_real_authority_loading_browsing_and_refresh_never_rewrite_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            document = root / "article.md"
            references = root / "references.md"
            sets = root / "reference-sets.md"
            document.write_text("# Intro {#intro}\nText [@alpha].\n", encoding="utf-8")
            reference_store = MarkdownReferenceStore(str(references))
            reference_store.save((record("alpha", "Alpha"),), reference_store.load().token)
            set_store = MarkdownReferenceSetStore(str(sets))
            set_store.save((ReferenceSet("Core", members=("alpha",)),), set_store.load().token)
            note_store = MarkdownSourceNoteStore(source_notes_path(str(document)))
            note_store.save((note("note-1"),), note_store.load().token)

            paths = (document, references, sets, Path(source_notes_path(str(document))))
            before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
            provider = lambda: build_document_dossier_inputs(
                document_text=document.read_text(encoding="utf-8"),
                document_path=str(document),
                modified=False,
                bookmarks=(0,),
                reference_store=reference_store,
                reference_set_store=set_store,
            )
            controller = DocumentDossierController(provider)
            runtime = DocumentOverviewRuntime(
                object(), controller,
                navigate_offset=lambda _value: True,
                select_range=lambda _start, _end: True,
                show_reference=lambda _key: True,
                show_source_note=lambda _key: True,
                show_reference_set=lambda _name: True,
                run_research_check=lambda: True,
                focus_document=lambda: True,
                show_error=lambda _message: None,
                show_notice=lambda _message: None,
                view_factory=lambda _parent: FakeView(),
            )
            runtime.open()
            for category in ("overview", "structure", "research", "integrity", "statistics"):
                runtime.select_category(category)
            runtime.refresh()
            runtime.close()
            after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
            self.assertEqual(before, after)

    def test_malformed_authorities_are_loaded_read_only_without_rewrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            document = root / "article.md"
            references = root / "references.md"
            sets = root / "reference-sets.md"
            sidecar = Path(source_notes_path(str(document)))
            document.write_text("# Intro\n[@missing]\n", encoding="utf-8")
            references.write_text("## bad key\nTitle: Bad\n", encoding="utf-8")
            sets.write_text("## Set\n- missing\n- missing\n", encoding="utf-8")
            sidecar.write_text("## Source Note: bad id\nKind: quote\n", encoding="utf-8")
            paths = (document, references, sets, sidecar)
            before = {path: path.read_bytes() for path in paths}
            inputs = build_document_dossier_inputs(
                document_text=document.read_text(encoding="utf-8"),
                document_path=str(document),
                modified=False,
                bookmarks=(),
                reference_store=MarkdownReferenceStore(str(references)),
                reference_set_store=MarkdownReferenceSetStore(str(sets)),
            )
            snapshot = DocumentDossierController(lambda: inputs).refresh()
            self.assertGreater(len(snapshot.issues), 0)
            self.assertEqual(before, {path: path.read_bytes() for path in paths})


if __name__ == "__main__":
    unittest.main()
