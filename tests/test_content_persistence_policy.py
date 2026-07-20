import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "calamus" / "calamus_clips.py"
STATE = ROOT / "calamus" / "calamus_state.py"
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
