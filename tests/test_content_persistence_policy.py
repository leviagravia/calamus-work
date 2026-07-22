import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "calamus" / "calamus_clips.py"
STATE = ROOT / "calamus" / "calamus_state.py"
REFERENCES = ROOT / "calamus" / "calamus_reference_store.py"
SOURCE_NOTES = ROOT / "calamus" / "calamus_source_note_store.py"
RESEARCH_FILE = ROOT / "calamus" / "calamus_research_file.py"
SOURCE_DIR = ROOT / "calamus"


def source(path):
    return path.read_text(encoding="utf-8")


class ContentPersistencePolicyTests(unittest.TestCase):
    def test_user_clip_content_is_markdown_canonical_and_json_legacy_read_only(self):
        clips = source(CLIPS)
        self.assertIn('return os.path.join(config_dir, "clips.md")', clips)
        self.assertIn('return os.path.join(config_dir, "clips.json")', clips)
        self.assertIn("if os.path.exists(path):", clips)
        self.assertIn("save_clips(config_dir, legacy, limit)", clips)
        self.assertNotIn("save_json_file", clips)
        self.assertIn("read-only backup", clips)
        self.assertIn("never synchronized or rewritten", clips)

    def test_json_remains_allowed_for_technical_application_state(self):
        state = source(STATE)
        for filename in ("settings.json", "recent.json", "favourites.json"):
            self.assertIn(filename, state)
        self.assertIn("save_json_file", state)
        self.assertIn("JSON remains valid for technical application state", state)
        self.assertIn("canonical UTF-8 Markdown store", state)


    def test_references_are_global_utf8_markdown_not_json(self):
        references = source(REFERENCES)
        self.assertIn('"calamus", "research", "references.md"', references)
        self.assertIn('encoding="utf-8"', references)
        self.assertIn("atomic_write_utf8", references)
        research_file = source(RESEARCH_FILE)
        self.assertIn("os.replace(tmp_path, path)", research_file)
        self.assertIn("References file changed outside Calamus", references)
        self.assertNotIn("references.json", references)


    def test_source_notes_are_document_sidecar_markdown_not_json(self):
        source_notes = source(SOURCE_NOTES)
        self.assertIn('".source-notes.md"', source_notes)
        self.assertIn('"# Calamus Source Notes v1"', source_notes)
        self.assertIn("atomic_write_utf8", source_notes)
        self.assertNotIn("source-notes.json", source_notes)

    def test_no_research_content_json_store_is_declared(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SOURCE_DIR.glob("*.py")
        ).lower()
        for forbidden in (
            "references.json",
            "source-notes.json",
            "scratchpad.json",
            "concepts.json",
            "tags.json",
            "research.json",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
