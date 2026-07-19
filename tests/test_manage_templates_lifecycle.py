import os
from pathlib import Path
import stat
import tempfile
import unittest

from calamus_templates import (
    DEFAULT_TEMPLATE_NAME,
    DeleteTemplatePlan,
    ManagedTemplateEntry,
    RenameTemplatePlan,
    delete_template_file,
    ensure_templates_dir,
    list_managed_templates,
    list_templates,
    prepare_delete_template_plan,
    prepare_rename_template_plan,
    rename_template_file,
)


class ManageTemplatesDomainTests(unittest.TestCase):
    def _write(self, path, text="Body"):
        Path(path).write_text(text, encoding="utf-8")

    def test_managed_listing_is_sorted_regular_no_follow_and_marks_default(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            self._write(os.path.join(store, "Zulu.txt"), "Z")
            self._write(os.path.join(store, "alpha.md"), "A")
            self._write(os.path.join(store, "ignore.rtf"), "R")
            os.mkdir(os.path.join(store, "folder.txt"))
            os.symlink(os.path.join(store, "alpha.md"), os.path.join(store, "link.md"))

            entries = list_managed_templates(td)
            self.assertTrue(all(isinstance(item, ManagedTemplateEntry) for item in entries))
            self.assertEqual([item.name for item in entries], ["alpha.md", DEFAULT_TEMPLATE_NAME, "Zulu.txt"])
            protected = {item.name: item.protected for item in entries}
            self.assertTrue(protected[DEFAULT_TEMPLATE_NAME])
            self.assertFalse(protected["alpha.md"])
            self.assertEqual(
                list_templates(td),
                [(item.name, item.path) for item in entries],
            )

    def test_rename_plan_accepts_direct_regular_user_template(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            source = os.path.join(store, "letter.txt")
            self._write(source, "Letter")
            plan = prepare_rename_template_plan(td, source, "sermon.md")
            self.assertIsInstance(plan, RenameTemplatePlan)
            self.assertEqual(plan.source_name, "letter.txt")
            self.assertEqual(plan.target_name, "sermon.md")
            self.assertEqual(plan.target_path, os.path.join(store, "sermon.md"))

    def test_rename_cancel_or_same_name_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            source = os.path.join(store, "letter.txt")
            self._write(source)
            self.assertIsNone(prepare_rename_template_plan(td, source, None))
            self.assertIsNone(prepare_rename_template_plan(td, source, "letter.txt"))
            self.assertTrue(os.path.exists(source))

    def test_rename_rejects_default_paths_extensions_collision_directory_and_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            source = os.path.join(store, "letter.txt")
            target = os.path.join(store, "target.md")
            self._write(source)
            self._write(target)
            with self.assertRaises(ValueError):
                prepare_rename_template_plan(td, os.path.join(store, DEFAULT_TEMPLATE_NAME), "new.txt")
            with self.assertRaises(ValueError):
                prepare_rename_template_plan(td, source, "../escape.txt")
            with self.assertRaises(ValueError):
                prepare_rename_template_plan(td, source, "nested/name.txt")
            with self.assertRaises(ValueError):
                prepare_rename_template_plan(td, source, "bad.rtf")
            with self.assertRaises(FileExistsError):
                prepare_rename_template_plan(td, source, "target.md")
            directory = os.path.join(store, "folder.txt")
            os.mkdir(directory)
            with self.assertRaises(ValueError):
                prepare_rename_template_plan(td, directory, "folder2.txt")
            link = os.path.join(store, "link.txt")
            os.symlink(source, link)
            with self.assertRaises(ValueError):
                prepare_rename_template_plan(td, link, "link2.txt")

    def test_rename_preserves_contents_mode_and_removes_old_name(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            source = os.path.join(store, "letter.txt")
            self._write(source, "città\n")
            os.chmod(source, 0o640)
            plan = prepare_rename_template_plan(td, source, "sermon.md")
            target = rename_template_file(plan)
            self.assertFalse(os.path.exists(source))
            self.assertEqual(Path(target).read_text(encoding="utf-8"), "città\n")
            self.assertEqual(stat.S_IMODE(os.stat(target).st_mode), 0o640)

    def test_rename_executor_revalidates_plan_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            source = os.path.join(store, "letter.txt")
            self._write(source, "source")
            outside = os.path.join(td, "outside.txt")
            forged = RenameTemplatePlan(store, source, outside, "letter.txt", "outside.txt")
            with self.assertRaises(ValueError):
                rename_template_file(forged)
            target = os.path.join(store, "target.txt")
            plan = prepare_rename_template_plan(td, source, "target.txt")
            self._write(target, "existing")
            with self.assertRaises(FileExistsError):
                rename_template_file(plan)
            self.assertEqual(Path(source).read_text(encoding="utf-8"), "source")
            self.assertEqual(Path(target).read_text(encoding="utf-8"), "existing")
            with self.assertRaises(TypeError):
                rename_template_file(object())

    def test_rename_executor_rejects_source_mutated_to_symlink_after_plan(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            source = os.path.join(store, "letter.txt")
            referent = os.path.join(store, "referent.txt")
            self._write(source, "original")
            self._write(referent, "referent")
            plan = prepare_rename_template_plan(td, source, "renamed.txt")
            os.unlink(source)
            os.symlink(referent, source)
            with self.assertRaises(ValueError):
                rename_template_file(plan)
            self.assertTrue(os.path.islink(source))
            self.assertFalse(os.path.exists(os.path.join(store, "renamed.txt")))
            self.assertEqual(Path(referent).read_text(encoding="utf-8"), "referent")

    def test_delete_plan_accepts_user_template_and_executor_removes_it(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            target = os.path.join(store, "letter.txt")
            self._write(target)
            plan = prepare_delete_template_plan(td, target)
            self.assertIsInstance(plan, DeleteTemplatePlan)
            self.assertEqual(delete_template_file(plan), target)
            self.assertFalse(os.path.lexists(target))

    def test_delete_rejects_default_outside_directory_symlink_and_forged_plan(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            with self.assertRaises(ValueError):
                prepare_delete_template_plan(td, os.path.join(store, DEFAULT_TEMPLATE_NAME))
            outside = os.path.join(td, "outside.txt")
            self._write(outside)
            with self.assertRaises(ValueError):
                prepare_delete_template_plan(td, outside)
            directory = os.path.join(store, "folder.txt")
            os.mkdir(directory)
            with self.assertRaises(ValueError):
                prepare_delete_template_plan(td, directory)
            source = os.path.join(store, "source.txt")
            self._write(source)
            link = os.path.join(store, "link.txt")
            os.symlink(source, link)
            with self.assertRaises(ValueError):
                prepare_delete_template_plan(td, link)
            forged = DeleteTemplatePlan(store, outside, "outside.txt")
            with self.assertRaises(ValueError):
                delete_template_file(forged)
            self.assertTrue(os.path.exists(outside))
            with self.assertRaises(TypeError):
                delete_template_file(object())

    def test_delete_executor_rejects_target_mutated_to_symlink_after_plan(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            target = os.path.join(store, "letter.txt")
            referent = os.path.join(store, "referent.txt")
            self._write(target, "original")
            self._write(referent, "referent")
            plan = prepare_delete_template_plan(td, target)
            os.unlink(target)
            os.symlink(referent, target)
            with self.assertRaises(ValueError):
                delete_template_file(plan)
            self.assertTrue(os.path.islink(target))
            self.assertEqual(Path(referent).read_text(encoding="utf-8"), "referent")

    def test_default_name_remains_stable_but_content_can_exist(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            default = os.path.join(store, DEFAULT_TEMPLATE_NAME)
            Path(default).write_text("Customized", encoding="utf-8")
            entries = list_managed_templates(td)
            found = next(item for item in entries if item.name == DEFAULT_TEMPLATE_NAME)
            self.assertTrue(found.protected)
            self.assertEqual(Path(found.path).read_text(encoding="utf-8"), "Customized")


if __name__ == "__main__":
    unittest.main()
