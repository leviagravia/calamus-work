import os
from pathlib import Path
import stat
import tempfile
import unittest

from calamus_templates import (
    SaveTemplatePlan,
    ensure_templates_dir,
    prepare_save_template_plan,
    suggest_template_filename,
    write_template_atomic,
)


class SaveTemplatePlanTests(unittest.TestCase):
    def test_filename_suggestion_preserves_supported_suffix(self):
        self.assertEqual(suggest_template_filename('/tmp/letter.md'), 'letter.md')
        self.assertEqual(suggest_template_filename('/tmp/letter.txt'), 'letter.txt')

    def test_filename_suggestion_converts_other_suffix_or_untitled(self):
        self.assertEqual(suggest_template_filename('/tmp/letter.rtf'), 'letter.txt')
        self.assertEqual(suggest_template_filename(None), 'template.txt')
        self.assertEqual(suggest_template_filename(''), 'template.txt')

    def test_plan_accepts_direct_supported_child_and_preserves_text(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            target = os.path.join(store, 'sermon.md')
            plan = prepare_save_template_plan(td, target, 'Heading\n')
            self.assertIsInstance(plan, SaveTemplatePlan)
            self.assertEqual(plan.store_dir, store)
            self.assertEqual(plan.target_path, target)
            self.assertEqual(plan.text, 'Heading\n')
            self.assertFalse(plan.replaces_existing)

    def test_cancel_returns_no_plan(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(prepare_save_template_plan(td, None, 'Body'))
            self.assertIsNone(prepare_save_template_plan(td, '', 'Body'))

    def test_plan_requires_supported_extension(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            with self.assertRaises(ValueError):
                prepare_save_template_plan(td, os.path.join(store, 'sermon'), 'Body')
            with self.assertRaises(ValueError):
                prepare_save_template_plan(td, os.path.join(store, 'sermon.rtf'), 'Body')

    def test_plan_rejects_escape_and_nested_subdirectory(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            outside = os.path.join(td, 'outside.txt')
            nested = os.path.join(store, 'nested')
            os.mkdir(nested)
            with self.assertRaises(ValueError):
                prepare_save_template_plan(td, outside, 'Body')
            with self.assertRaises(ValueError):
                prepare_save_template_plan(td, os.path.join(nested, 'note.txt'), 'Body')
            with self.assertRaises(ValueError):
                prepare_save_template_plan(td, os.path.join(store, '..', 'escape.txt'), 'Body')

    def test_plan_rejects_directory_and_symlink_targets(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            directory = os.path.join(store, 'folder.md')
            os.mkdir(directory)
            with self.assertRaises(ValueError):
                prepare_save_template_plan(td, directory, 'Body')
            source = os.path.join(store, 'source.txt')
            Path(source).write_text('old', encoding='utf-8')
            link = os.path.join(store, 'link.txt')
            os.symlink(source, link)
            with self.assertRaises(ValueError):
                prepare_save_template_plan(td, link, 'Body')

    def test_existing_regular_file_is_explicit_overwrite_plan(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            target = os.path.join(store, 'letter.txt')
            Path(target).write_text('old', encoding='utf-8')
            plan = prepare_save_template_plan(td, target, 'new')
            self.assertTrue(plan.replaces_existing)

    def test_atomic_write_creates_exact_utf8_text_and_no_temp_files(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            target = os.path.join(store, 'letter.txt')
            plan = prepare_save_template_plan(td, target, 'città\nβ\n')
            self.assertEqual(write_template_atomic(plan), target)
            self.assertEqual(Path(target).read_text(encoding='utf-8'), 'città\nβ\n')
            self.assertFalse(any(name.startswith('.calamus-template-') for name in os.listdir(store)))

    def test_atomic_overwrite_preserves_existing_mode(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            target = os.path.join(store, 'letter.txt')
            Path(target).write_text('old', encoding='utf-8')
            os.chmod(target, 0o640)
            plan = prepare_save_template_plan(td, target, 'new')
            write_template_atomic(plan)
            self.assertEqual(Path(target).read_text(encoding='utf-8'), 'new')
            self.assertEqual(stat.S_IMODE(os.stat(target).st_mode), 0o640)

    def test_atomic_writer_rechecks_plan_store_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            outside = os.path.join(td, 'outside.txt')
            forged = SaveTemplatePlan(
                store_dir=store,
                target_path=outside,
                text='Body',
                replaces_existing=False,
            )
            with self.assertRaises(ValueError):
                write_template_atomic(forged)
            self.assertFalse(os.path.exists(outside))

    def test_atomic_write_rejects_wrong_plan_type(self):
        with self.assertRaises(TypeError):
            write_template_atomic(object())

    def test_non_string_inputs_fail_before_write(self):
        with tempfile.TemporaryDirectory() as td:
            store = ensure_templates_dir(td)
            target = os.path.join(store, 'letter.txt')
            with self.assertRaises(TypeError):
                prepare_save_template_plan(td, 123, 'Body')
            with self.assertRaises(TypeError):
                prepare_save_template_plan(td, target, None)
            with self.assertRaises(TypeError):
                suggest_template_filename(123)


if __name__ == '__main__':
    unittest.main()
