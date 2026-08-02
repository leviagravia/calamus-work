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

    def test_workspace_mutation_scope_is_bounded_to_create_rename_duplicate_and_system_trash(self):
        combined='\n'.join((ROOT/'calamus'/name).read_text(encoding='utf-8') for name in (
            'calamus_workspace.py','calamus_workspace_controller.py','calamus_workspace_application.py',
            'calamus_workspace_tree.py','calamus_workspace_panel.py',
            'calamus_workspace_operations.py','calamus_workspace_gio.py',
            'calamus_workspace_mutation.py','calamus_workspace_identity.py'))
        self.assertIn('new-text-file', combined)
        self.assertIn('new-folder', combined)
        self.assertIn('duplicate-text-file', combined)
        self.assertIn('move-to-trash', combined)
        self.assertIn('target.create(Gio.FileCreateFlags.NONE, None)', combined)
        self.assertIn('source.trash(None)', combined)
        for forbidden in ('os.remove','os.unlink','shutil.move','copytree','send2trash',
                          'Gio.FileMonitor','make_directory_with_parents'):
            self.assertNotIn(forbidden,combined)

    def test_chooser_and_panel_are_unambiguously_distinct(self):
        dialogs=(ROOT/'calamus/calamus_dialogs.py').read_text(encoding='utf-8')
        panel=(ROOT/'calamus/calamus_workspace_panel.py').read_text(encoding='utf-8')
        self.assertIn('Set Writing Workspace Folder',dialogs)
        self.assertIn('This window sets the Workspace folder; it does not open files.',dialogs)
        self.assertIn('Set Current Folder as Workspace',dialogs)
        self.assertIn('folder_filter.add_custom',dialogs)
        self.assertIn('dialog.get_current_folder()',dialogs)
        self.assertIn('Open, create, rename, duplicate and trash · bounded writing tree',panel)
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

    def test_menu_exposes_create_rename_duplicate_and_system_trash_only(self):
        ui=(ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8')
        start=ui.index('app.workspace_file_item = Gtk.MenuItem(label="Writing Workspace")')
        end=ui.index('add_separator(filem)', start)
        workspace_menu=ui[start:end]
        self.assertIn('New Text File…', workspace_menu)
        self.assertIn('New Folder…', workspace_menu)
        self.assertIn('Rename Selected Item…', workspace_menu)
        self.assertIn('Duplicate Selected Text File', workspace_menu)
        self.assertIn('Move Selected Item to Trash', workspace_menu)
        self.assertIn('Change Workspace Folder…',workspace_menu)
        self.assertIn('Show Workspace Panel',workspace_menu)
        self.assertIn('Close Workspace',workspace_menu)
        for forbidden in ('Permanently Delete', 'Duplicate Folder',
                          'Delete Workspace', 'Copy Workspace', 'Move Workspace'):
            self.assertNotIn(forbidden,workspace_menu)

    def test_file_menu_groups_workspace_commands_in_one_submenu(self):
        ui=(ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8')
        self.assertIn('app.workspace_file_item = Gtk.MenuItem(label="Writing Workspace")',ui)
        self.assertIn('app.workspace_file_item.set_submenu(app.workspace_file_menu)',ui)
        for label in ('Show Workspace Panel','New Text File…','New Folder…','Rename Selected Item…','Duplicate Selected Text File','Move Selected Item to Trash','Change Workspace Folder…','Recent Workspaces','Rescan Folder Contents','Reveal Workspace Folder in File Manager','Close Workspace'):
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


    def test_new_text_file_uses_pure_plan_one_gio_commit_and_reconciliation(self):
        planner=(ROOT/'calamus/calamus_workspace_operations.py').read_text(encoding='utf-8')
        adapter=(ROOT/'calamus/calamus_workspace_gio.py').read_text(encoding='utf-8')
        runtime=(ROOT/'calamus/calamus_workspace_mutation.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        panel=(ROOT/'calamus/calamus_workspace_panel.py').read_text(encoding='utf-8')
        self.assertNotIn('gi.repository', planner)
        self.assertNotIn('Gtk', planner)
        self.assertIn('WorkspaceOperationPlan', planner)
        self.assertIn('target.create(Gio.FileCreateFlags.NONE, None)', adapter)
        self.assertIn('if not self._may_continue():', runtime)
        self.assertLess(runtime.index('if not self._may_continue():'), runtime.index('result = self._controller.execute(plan)'))
        self.assertIn('self._workspace_runtime.refresh()', runtime)
        self.assertIn('self._view.select_path(result.path)', runtime)
        self.assertIn('self._open_document(result.path)', runtime)
        self.assertIn('WorkspaceMutationRuntime(', launcher)
        self.assertIn('open_document=self.open_path', launcher)
        self.assertIn('document-new-symbolic', panel)

    def test_new_text_file_dialog_is_input_only(self):
        dialogs=(ROOT/'calamus/calamus_dialogs.py').read_text(encoding='utf-8')
        block=dialogs[dialogs.index('def prompt_new_workspace_text_file'):dialogs.index('def choose_save_file')]
        self.assertIn('New Text File in Writing Workspace', block)
        self.assertIn('Create and Open', block)
        self.assertIn('Plain text (.txt)', block)
        self.assertIn('Markdown (.md)', block)
        for forbidden in ('Gio.File', 'open(', 'write(', 'os.mkdir', 'os.rename'):
            self.assertNotIn(forbidden, block)


    def test_new_folder_uses_pure_plan_one_gio_commit_and_reconciliation(self):
        planner=(ROOT/'calamus/calamus_workspace_operations.py').read_text(encoding='utf-8')
        adapter=(ROOT/'calamus/calamus_workspace_gio.py').read_text(encoding='utf-8')
        runtime=(ROOT/'calamus/calamus_workspace_mutation.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        panel=(ROOT/'calamus/calamus_workspace_panel.py').read_text(encoding='utf-8')
        self.assertIn('def plan_new_folder(', planner)
        self.assertIn('kind="new-folder"', planner)
        self.assertIn('open_after_commit=False', planner)
        self.assertIn('target.make_directory(None)', adapter)
        self.assertNotIn('make_directory_with_parents', adapter)
        block=runtime[runtime.index('def create_new_folder('):]
        self.assertNotIn('self._may_continue()', block)
        self.assertIn('self._workspace_runtime.refresh()', block)
        self.assertIn('self._view.select_path(result.path)', block)
        self.assertNotIn('self._open_document(result.path)', block)
        self.assertIn('def create_workspace_folder(self, name):', launcher)
        self.assertIn('folder-new-symbolic', panel)

    def test_new_folder_dialog_is_input_only(self):
        dialogs=(ROOT/'calamus/calamus_dialogs.py').read_text(encoding='utf-8')
        block=dialogs[dialogs.index('def prompt_new_workspace_folder'):dialogs.index('def choose_save_file')]
        self.assertIn('New Folder in Writing Workspace', block)
        self.assertIn('Create Folder', block)
        self.assertIn('Folder name:', block)
        for forbidden in ('Gio.File', 'open(', 'write(', 'os.mkdir', 'os.rename', 'make_directory'):
            self.assertNotIn(forbidden, block)


    def test_rename_uses_pure_plan_gio_set_display_name_and_identity_reconciliation(self):
        planner=(ROOT/'calamus/calamus_workspace_operations.py').read_text(encoding='utf-8')
        adapter=(ROOT/'calamus/calamus_workspace_gio.py').read_text(encoding='utf-8')
        runtime=(ROOT/'calamus/calamus_workspace_mutation.py').read_text(encoding='utf-8')
        identity=(ROOT/'calamus/calamus_workspace_identity.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('class WorkspaceRenamePlan', planner)
        self.assertIn('def plan_workspace_rename(', planner)
        self.assertNotIn('os.rename', planner)
        self.assertIn('.set_display_name(', adapter)
        self.assertIn('def rename_item(', runtime)
        block=runtime[runtime.index('def rename_item('):]
        self.assertNotIn('self._may_continue()', block)
        self.assertIn('self._workspace_runtime.refresh()', block)
        self.assertIn('self._reconcile_rename(plan, references)', block)
        self.assertIn('def plan_workspace_rename_identity(', identity)
        self.assertIn('self.document.file_path = identity.current_file_after', launcher)
        self.assertIn('getattr(self, "research_document_context_changed", lambda: None)()', launcher)
        self.assertIn('self.state.save_recent_files', launcher)
        self.assertIn('self.state.save_favourites', launcher)


    def test_duplicate_uses_pure_plan_gio_copy_and_reconciliation_without_identity_transfer(self):
        planner=(ROOT/'calamus/calamus_workspace_operations.py').read_text(encoding='utf-8')
        adapter=(ROOT/'calamus/calamus_workspace_gio.py').read_text(encoding='utf-8')
        runtime=(ROOT/'calamus/calamus_workspace_mutation.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('class WorkspaceDuplicatePlan', planner)
        self.assertIn('def next_duplicate_text_name(', planner)
        self.assertIn('def plan_duplicate_text_file(', planner)
        self.assertNotIn('shutil.copy', planner)
        self.assertIn('source.copy(target, Gio.FileCopyFlags.NONE, None, None)', adapter)
        self.assertIn('def duplicate_text_file(', runtime)
        block=runtime[runtime.index('def duplicate_text_file('):runtime.index('def rename_item(')]
        self.assertNotIn('self._may_continue()', block)
        self.assertNotIn('self._open_document(', block)
        self.assertIn('self._workspace_runtime.refresh()', block)
        self.assertIn('self._view.select_path(result.path)', block)
        self.assertIn('def on_duplicate_workspace_file(', launcher)
        self.assertNotIn('self.current_file =', block)

    def test_context_menu_is_selection_adapter_to_canonical_rename_gateway(self):
        tree=(ROOT/'calamus/calamus_workspace_tree.py').read_text(encoding='utf-8')
        panel=(ROOT/'calamus/calamus_workspace_panel.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('self.connect("button-press-event", self._on_button_press)', tree)
        self.assertIn('self.connect("popup-menu", self._on_popup_menu)', tree)
        self.assertIn('self.selection.select_path(tree_path)', tree)
        self.assertIn('self.emit("item-context-menu", item, event)', tree)
        self.assertIn('Gtk.MenuItem(label="Rename…")', panel)
        self.assertIn('Gtk.MenuItem(label="Duplicate")', panel)
        self.assertIn('Gtk.MenuItem(label="Move to Trash")', panel)
        self.assertIn('self._on_rename_item()', panel)
        self.assertIn('self._on_duplicate_file()', panel)
        self.assertIn('self._on_move_to_trash()', panel)
        self.assertIn('item.internal_text', panel)
        self.assertIn('Gdk.Gravity.SOUTH_WEST', panel)
        self.assertNotIn('Gtk.Gravity.', panel)
        self.assertIn('on_rename_item=self.on_rename_workspace_item', launcher)
        self.assertIn('on_duplicate_file=self.on_duplicate_workspace_file', launcher)
        self.assertIn('on_move_to_trash=self.on_move_workspace_item_to_trash', launcher)
        for forbidden in ('Gio.File', 'set_display_name', 'os.rename', 'shutil.move'):
            self.assertNotIn(forbidden, panel)

    def test_rename_dialog_is_input_only_and_prefills_current_name(self):
        dialogs=(ROOT/'calamus/calamus_dialogs.py').read_text(encoding='utf-8')
        block=dialogs[dialogs.index('def prompt_rename_workspace_item'):dialogs.index('def choose_save_file')]
        self.assertIn('Rename {kind} in Writing Workspace', block)
        self.assertIn('entry.set_text(current_name)', block)
        self.assertIn('entry.select_region', block)
        for forbidden in ('Gio.File', 'os.rename', 'set_display_name', 'shutil.move'):
            self.assertNotIn(forbidden, block)

    def test_rename_scope_rejects_bulk_delete_and_root_rename(self):
        planner=(ROOT/'calamus/calamus_workspace_operations.py').read_text(encoding='utf-8')
        block=planner[planner.index('def plan_workspace_rename('):planner.index('def _truncate_utf8_component')]
        self.assertIn('The Workspace root itself cannot be renamed here.', block)
        self.assertIn('Select one Workspace file or folder to rename.', block)
        for forbidden in ('bulk rename','MovePlan','delete_permanently','send2trash'):
            self.assertNotIn(forbidden, block)

    def test_move_to_trash_uses_pure_plan_gio_system_trash_and_identity_reconciliation(self):
        planner=(ROOT/'calamus/calamus_workspace_operations.py').read_text(encoding='utf-8')
        adapter=(ROOT/'calamus/calamus_workspace_gio.py').read_text(encoding='utf-8')
        runtime=(ROOT/'calamus/calamus_workspace_mutation.py').read_text(encoding='utf-8')
        identity=(ROOT/'calamus/calamus_workspace_identity.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        dialogs=(ROOT/'calamus/calamus_dialogs.py').read_text(encoding='utf-8')
        self.assertIn('class WorkspaceTrashPlan', planner)
        self.assertIn('def plan_move_to_trash(', planner)
        self.assertNotIn('gi.repository', planner)
        trash_block=adapter[adapter.index('def move_to_trash('):]
        self.assertIn('source.trash(None)', trash_block)
        self.assertIn('companion.trash(None)', trash_block)
        self.assertNotIn('.delete(', trash_block)
        self.assertNotIn('os.unlink', trash_block)
        self.assertNotIn('os.remove', trash_block)
        self.assertIn('def move_to_trash(', runtime)
        self.assertIn('self._confirm_trash(plan, active_affected)', runtime)
        self.assertIn('self._reconcile_trash(plan, references)', runtime)
        self.assertIn('def plan_workspace_trash_identity(', identity)
        self.assertIn('self.document.file_path = None', launcher)
        self.assertIn('self.document.set_text(current_text, modified=True)', launcher)
        self.assertIn('Move Selected Item to Trash', (ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8'))
        self.assertIn('def confirm_move_workspace_item_to_trash(', dialogs)
        dialog_block=dialogs[dialogs.index('def confirm_move_workspace_item_to_trash('):]
        for forbidden in ('Gio.File', 'os.unlink', 'os.remove', '.trash('):
            self.assertNotIn(forbidden, dialog_block)

    def test_trash_context_action_is_capability_adapter_and_no_permanent_delete_exists(self):
        panel=(ROOT/'calamus/calamus_workspace_panel.py').read_text(encoding='utf-8')
        ui=(ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8')
        self.assertIn('if not item.is_symlink and not item.managed_sidecar:', panel)
        self.assertIn('Gtk.MenuItem(label="Move to Trash")', panel)
        self.assertIn('self._on_move_to_trash()', panel)
        self.assertNotIn('Permanently Delete', panel + ui)
        self.assertNotIn('Delete Selected Item', panel + ui)

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
