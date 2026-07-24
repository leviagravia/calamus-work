from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WorkspaceCommandWiringTests(unittest.TestCase):
    def test_mature_source_boundary_is_present_in_code(self):
        view=(ROOT/'calamus/calamus_workspace_tree.py').read_text(encoding='utf-8')
        app=(ROOT/'calamus/calamus_workspace_application.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('self.connect("row-activated", self._on_row_activated)',view)
        self.assertIn('self.connect("key-press-event", self._on_key_press)',view)
        self.assertIn('self.emit("file-activated", item)',view)
        self.assertIn('column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)',view)
        self.assertIn('column.set_fixed_width(1)',view)
        self.assertIn('column.set_expand(True)',view)
        self.assertIn('open_document=self.open_path',launcher)
        self.assertIn('self._open_document(activation.path)',app)

    def test_view_is_semantic_and_has_no_document_or_filesystem_ownership(self):
        view=(ROOT/'calamus/calamus_workspace_tree.py').read_text(encoding='utf-8')
        for forbidden in ('open(', 'subprocess', 'os.scandir', 'read_text_file', 'App.open_path'):
            self.assertNotIn(forbidden,view)

    def test_workspace_scope_is_read_only(self):
        combined='\n'.join((ROOT/'calamus'/name).read_text(encoding='utf-8') for name in (
            'calamus_workspace.py','calamus_workspace_controller.py','calamus_workspace_application.py',
            'calamus_workspace_tree.py','calamus_workspace_panel.py'))
        for forbidden in ('os.rename','os.remove','os.unlink','shutil.move','copytree','send2trash','Gio.FileMonitor'):
            self.assertNotIn(forbidden,combined)

    def test_chooser_and_panel_are_unambiguously_distinct(self):
        dialogs=(ROOT/'calamus/calamus_dialogs.py').read_text(encoding='utf-8')
        panel=(ROOT/'calamus/calamus_workspace_panel.py').read_text(encoding='utf-8')
        self.assertIn('Set Writing Workspace Folder',dialogs)
        self.assertIn('This window sets the Workspace folder; it does not open files.',dialogs)
        self.assertIn('Set Current Folder as Workspace',dialogs)
        self.assertIn('folder_filter.add_custom',dialogs)
        self.assertIn('dialog.get_current_folder()',dialogs)
        self.assertIn('Open files here · double-click or Enter · read-only tree',panel)
        self.assertIn('os.path.basename(snapshot.root.rstrip(os.sep))',panel)
        self.assertIn('self.root_label.set_max_width_chars(24)',panel)
        self.assertIn('self.scroll.set_propagate_natural_width(False)',panel)

    def test_light_and_dark_contrast_are_explicit(self):
        css=(ROOT/'calamus/calamus_appearance.py').read_text(encoding='utf-8')
        self.assertGreaterEqual(css.count('#calamus-workspace-tree'),4)
        self.assertIn('color: #111111',css)
        self.assertIn('color: #f7f7f7',css)
        self.assertIn('color: @theme_text_color',css)
        self.assertIn('background-color: @theme_base_color',css)

    def test_startup_visibility_is_applied_after_paned_zeroing(self):
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        zero=launcher.index('self.workspace_paned.set_position(0)')
        visible=launcher.index('if startup_workspace_visible:')
        self.assertLess(zero,visible)

    def test_menu_exposes_no_mutating_workspace_commands(self):
        ui=(ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8')
        self.assertIn('Change Workspace Folder…',ui)
        self.assertIn('Show Workspace Panel',ui)
        self.assertIn('Close Workspace',ui)
        for forbidden in ('New Workspace File','Rename Workspace','Move Workspace','Delete Workspace','Trash Workspace'):
            self.assertNotIn(forbidden,ui)

    def test_file_menu_groups_workspace_commands_in_one_submenu(self):
        ui=(ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8')
        self.assertIn('app.workspace_file_item = Gtk.MenuItem(label="Writing Workspace")',ui)
        self.assertIn('app.workspace_file_item.set_submenu(app.workspace_file_menu)',ui)
        for label in ('Show Workspace Panel','Change Workspace Folder…','Recent Workspaces','Rescan Folder Contents','Reveal Workspace Folder in File Manager','Close Workspace'):
            self.assertIn(label,ui)
        top_level_block=ui[ui.index('app.workspace_file_item ='):ui.index('add_separator(filem)',ui.index('app.workspace_file_item ='))]
        self.assertNotIn('add_item(filem, "Refresh Writing Workspace"',top_level_block)

    def test_left_panel_follows_xed_shrinkable_paned_boundary(self):
        host=(ROOT/'calamus/calamus_left_panel.py').read_text(encoding='utf-8')
        self.assertIn('self._paned.pack1(widget, False, True)',host)
        self.assertIn('widget.set_size_request(-1, -1)',host)
        self.assertNotIn('widget.set_size_request(panel_width, -1)',host)

    def test_refresh_preserves_tree_navigation_context(self):
        tree=(ROOT/'calamus/calamus_workspace_tree.py').read_text(encoding='utf-8')
        self.assertIn('expanded = self.expanded_relative_paths()',tree)
        self.assertIn('selected_relative = selected.relative_path',tree)
        self.assertIn('self.expand_row(tree_path, False)',tree)

    def test_all_root_commands_converge_on_one_operational_gateway(self):
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('self.activate_workspace_path,', launcher)
        self.assertIn('return self.activate_workspace_path(selected)', launcher)
        self.assertIn('def activate_workspace_path(self, path):', launcher)
        self.assertIn('self.workspace_panel_runtime.set_visible(True)', launcher)
        self.assertIn('self.workspace_panel_view.focus_tree()', launcher)

    def test_rescan_is_named_and_explained_as_external_change_refresh(self):
        ui=(ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8')
        panel=(ROOT/'calamus/calamus_workspace_panel.py').read_text(encoding='utf-8')
        self.assertIn('Rescan Folder Contents', ui)
        self.assertIn('Rescan after files or folders changed outside Calamus', panel)
        self.assertNotIn('"Refresh", app.on_refresh_workspace', ui)

    def test_toplevel_geometry_uses_wm_hints_not_widget_size_request(self):
        launcher = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
        self.assertIn("self.set_default_size(width, height)", launcher)
        self.assertIn("self.apply_window_geometry_hints()", launcher)
        self.assertNotIn(
            "self.set_size_request(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)",
            launcher,
        )

    def test_status_line_is_bounded_and_does_not_export_full_path(self):
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('self.status.set_ellipsize(Pango.EllipsizeMode.END)', launcher)
        self.assertIn('self.status.set_single_line_mode(True)', launcher)
        self.assertIn('self.status.set_max_width_chars(72)', launcher)
        self.assertIn('self.status.set_size_request(1, -1)', launcher)
        self.assertIn('visible_name = os.path.basename(self.current_file)', launcher)
        self.assertIn('self.status.set_tooltip_text(full_status)', launcher)


if __name__=='__main__': unittest.main()
