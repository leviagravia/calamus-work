import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / 'bin' / 'calamus'
UI = ROOT / 'calamus' / 'calamus_ui.py'
DIALOGS = ROOT / 'calamus' / 'calamus_dialogs.py'
TEMPLATES = ROOT / 'calamus' / 'calamus_templates.py'


def _method_node(name: str):
    source = LAUNCHER.read_text(encoding='utf-8')
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return source, node
    raise AssertionError(f'method {name!r} not found')


def _method_source(name: str) -> str:
    source, node = _method_node(name)
    return ast.get_source_segment(source, node) or ''


def _compiled_method(name: str, namespace=None):
    _source, node = _method_node(name)
    isolated = copy.deepcopy(node)
    module = ast.Module(body=[isolated], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), 'exec'), scope)
    return scope[name]


class SaveTemplateCommandWiringTests(unittest.TestCase):
    def test_visible_command_is_after_save_as_and_before_favorites(self):
        ui = UI.read_text(encoding='utf-8')
        save_as = 'add_item(filem, "Save As…\\tCtrl+Shift+S", app.on_save_as)'
        save_template = 'add_item(filem, "Save as Template…", app.on_save_as_template)'
        favorites = 'app.favourites_item = Gtk.MenuItem(label="Favorites")'
        self.assertIn(save_template, ui)
        self.assertLess(ui.index(save_as), ui.index(save_template))
        self.assertLess(ui.index(save_template), ui.index(favorites))

    def test_dialog_is_confined_by_default_and_confirms_overwrite(self):
        dialogs = DIALOGS.read_text(encoding='utf-8')
        tree = ast.parse(dialogs)
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'choose_save_template')
        source = ast.get_source_segment(dialogs, node) or ''
        self.assertIn('Gtk.FileChooserAction.SAVE', source)
        self.assertIn('dialog.set_do_overwrite_confirmation(True)', source)
        self.assertIn('dialog.set_current_folder(templates_dir)', source)
        self.assertIn('dialog.set_current_name(suggested_name)', source)
        self.assertIn('*.txt', source)
        self.assertIn('*.md', source)

    def test_template_module_owns_plan_and_atomic_writer_without_gtk(self):
        source = TEMPLATES.read_text(encoding='utf-8')
        self.assertIn('class SaveTemplatePlan', source)
        self.assertIn('def prepare_save_template_plan(', source)
        self.assertIn('def write_template_atomic(', source)
        self.assertIn('os.replace(temporary_path, target_path)', source)
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == 'gi' or name.startswith('gi.') for name in imports))
        self.assertNotIn('CommandLayer', source)

    def test_entrypoint_orders_dialog_plan_write_refresh_notification(self):
        method = _method_source('on_save_as_template')
        dialog_at = method.index('choose_save_template(')
        plan_at = method.index('prepare_save_template_plan(')
        write_at = method.index('write_template_atomic(plan)')
        refresh_at = method.index('self.populate_template_menu()')
        info_at = method.index('self.info(')
        self.assertLess(dialog_at, plan_at)
        self.assertLess(plan_at, write_at)
        self.assertLess(write_at, refresh_at)
        self.assertLess(refresh_at, info_at)
        for forbidden in (
            'self.current_file =',
            'self.document.file_path =',
            'self.modified =',
            'reset_undo_history',
            'set_cursor_offset',
            'select_range',
            'add_recent_file',
            'save_settings',
        ):
            self.assertNotIn(forbidden, method)

    def test_cancel_has_no_write_refresh_or_notification(self):
        events = []
        on_save = _compiled_method(
            'on_save_as_template',
            {
                'ensure_templates_dir': lambda config: events.append(('store', config)) or '/templates',
                'suggest_template_filename': lambda current: events.append(('suggest', current)) or 'note.txt',
                'choose_save_template': lambda *_args: events.append(('dialog',)) or None,
                'prepare_save_template_plan': lambda config, path, text: events.append(('plan', config, path, text)) or None,
                'write_template_atomic': lambda plan: events.append(('write', plan)),
                'os': __import__('os'),
                'OSError': OSError,
                'UnicodeError': UnicodeError,
            },
        )

        class State:
            config_dir = '/config'

        class App:
            state = State()
            current_file = '/docs/note.txt'
            def buffer_text(self):
                events.append(('buffer',))
                return 'Body'
            def error(self, message):
                events.append(('error', message))
            def populate_template_menu(self):
                events.append(('refresh',))
            def info(self, message):
                events.append(('info', message))

        self.assertFalse(on_save(App()))
        self.assertEqual(
            events,
            [('store', '/config'), ('suggest', '/docs/note.txt'), ('dialog',)],
        )

    def test_write_failure_reports_error_without_refresh_or_success(self):
        events = []
        plan = type('Plan', (), {'target_path': '/templates/note.txt'})()
        def fail_write(_plan):
            events.append(('write',))
            raise OSError('disk full')
        on_save = _compiled_method(
            'on_save_as_template',
            {
                'ensure_templates_dir': lambda _config: '/templates',
                'suggest_template_filename': lambda _current: 'note.txt',
                'choose_save_template': lambda *_args: '/templates/note.txt',
                'prepare_save_template_plan': lambda *_args: plan,
                'write_template_atomic': fail_write,
                'os': __import__('os'),
                'OSError': OSError,
                'UnicodeError': UnicodeError,
            },
        )

        class State:
            config_dir = '/config'

        class App:
            state = State()
            current_file = '/docs/note.txt'
            def buffer_text(self): return 'Body'
            def error(self, message): events.append(('error', message))
            def populate_template_menu(self): events.append(('refresh',))
            def info(self, message): events.append(('info', message))

        self.assertFalse(on_save(App()))
        self.assertEqual(events, [('write',), ('error', 'disk full')])

    def test_success_preserves_document_identity_and_editor_state(self):
        events = []
        plan = type('Plan', (), {'target_path': '/templates/note.txt'})()
        on_save = _compiled_method(
            'on_save_as_template',
            {
                'ensure_templates_dir': lambda _config: '/templates',
                'suggest_template_filename': lambda current: 'note.txt',
                'choose_save_template': lambda *_args: '/templates/note.txt',
                'prepare_save_template_plan': lambda config, path, text: plan,
                'write_template_atomic': lambda actual: events.append(('write', actual)),
                'os': __import__('os'),
                'OSError': OSError,
                'UnicodeError': UnicodeError,
            },
        )

        class State:
            config_dir = '/config'

        class Document:
            file_path = '/docs/original.txt'
            modified = True

        class App:
            state = State()
            document = Document()
            current_file = '/docs/original.txt'
            modified = True
            cursor = 7
            selection = (2, 5)
            undo_token = object()
            def buffer_text(self): return 'Body'
            def error(self, message): events.append(('error', message))
            def populate_template_menu(self): events.append(('refresh',))
            def info(self, message): events.append(('info', message))

        app = App()
        before = (
            app.document.file_path,
            app.current_file,
            app.modified,
            app.cursor,
            app.selection,
            app.undo_token,
        )
        self.assertTrue(on_save(app))
        after = (
            app.document.file_path,
            app.current_file,
            app.modified,
            app.cursor,
            app.selection,
            app.undo_token,
        )
        self.assertEqual(before, after)
        self.assertEqual(events, [('write', plan), ('refresh',), ('info', 'Template saved: note.txt')])

    def test_w60_does_not_add_manage_templates_or_touch_new_from_template(self):
        ui = UI.read_text(encoding='utf-8')
        self.assertNotIn('Manage Templates…', ui)
        new_method = _method_source('on_new_from_template')
        self.assertNotIn('prepare_save_template_plan', new_method)
        self.assertNotIn('write_template_atomic', new_method)


if __name__ == '__main__':
    unittest.main()
