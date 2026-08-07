"""Canonical W104 command/action catalog.

This is the single authoritative source for stable user-command identity,
default accelerators and shortcut-guide projection.  Execution bindings live
elsewhere.
"""
from __future__ import annotations

from calamus_command_registry import (
    CommandGuideEntry, CommandRegistry, CommandShortcut, CommandSpec,
)

def _shortcut(accelerator, display, **payload):
    return CommandShortcut(accelerator, display, tuple(sorted(payload.items())))

COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec(
        'edit.copy', 'Copy', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>C', 'Ctrl+C'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Copy', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Copy', 'Ctrl+C', ''),
        ),
    ),
    CommandSpec(
        'edit.cut', 'Cut', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>X', 'Ctrl+X'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Cut', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Cut', 'Ctrl+X', ''),
        ),
    ),
    CommandSpec(
        'edit.duplicate-line-selection', 'Duplicate Line / Selection', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>D', 'Ctrl+D'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Duplicate Line / Selection', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Duplicate Line / Selection', 'Ctrl+D', ''),
        ),
    ),
    CommandSpec(
        'edit.find-all', 'Find All…', menu_path='Edit',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Find All…', parameter_kind='',
    ),
    CommandSpec(
        'edit.find-next', 'Find Next', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>G', 'Ctrl+G'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Find Next', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Find Next', 'Ctrl+G', ''),
        ),
    ),
    CommandSpec(
        'edit.find-previous', 'Find Previous', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control><Shift>G', 'Ctrl+Shift+G'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Find Previous', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Find Previous', 'Ctrl+Shift+G', ''),
        ),
    ),
    CommandSpec(
        'edit.find-replace', 'Find / Replace', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>F', 'Ctrl+F'),
            _shortcut('<Control>H', 'Ctrl+H'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Find / Replace', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Find / Replace', 'Ctrl+F', ''),
            CommandGuideEntry('Edit', 'Replace', 'Ctrl+H', ''),
        ),
    ),
    CommandSpec(
        'edit.lowercase', 'Lowercase selection', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt><Shift>U', 'Ctrl+Alt+Shift+U'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Lowercase selection', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Lowercase selection', 'Ctrl+Alt+Shift+U', ''),
        ),
    ),
    CommandSpec(
        'edit.move-line', 'Move Line', menu_path='Edit',
        shortcuts=(
            _shortcut('<Alt>Up', 'Alt+Up', direction=-1),
            _shortcut('<Alt>Down', 'Alt+Down', direction=1),
        ),
        risk_class='low', flags=('parameterized',),
        description='Stable W104 command identity for Move Line', parameter_kind='direction',
    ),
    CommandSpec(
        'edit.paste', 'Paste', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>V', 'Ctrl+V'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Paste', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Paste', 'Ctrl+V', ''),
        ),
    ),
    CommandSpec(
        'edit.paste-clean-pdf', 'Paste Clean from PDF', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt>V', 'Ctrl+Alt+V'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Paste Clean from PDF', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Paste Clean from PDF', 'Ctrl+Alt+V', ''),
        ),
    ),
    CommandSpec(
        'edit.paste-plain', 'Paste as Plain Text', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control><Shift>V', 'Ctrl+Shift+V'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Paste as Plain Text', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Paste as Plain Text', 'Ctrl+Shift+V', ''),
        ),
    ),
    CommandSpec(
        'edit.redo', 'Redo', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>Y', 'Ctrl+Y'),
            _shortcut('<Control><Shift>Z', 'Ctrl+Shift+Z'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Redo', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Redo', 'Ctrl+Y / Ctrl+Shift+Z', ''),
        ),
    ),
    CommandSpec(
        'edit.replace-all', 'Replace All', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control><Shift>H', 'Ctrl+Shift+H'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Replace All', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Replace All', 'Ctrl+Shift+H', ''),
        ),
    ),
    CommandSpec(
        'edit.select-all', 'Select All', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>A', 'Ctrl+A'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Select All', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Select All', 'Ctrl+A', ''),
        ),
    ),
    CommandSpec(
        'edit.undo', 'Undo', menu_path='Edit',
        shortcuts=(
            _shortcut('<Control>Z', 'Ctrl+Z'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Undo', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Edit', 'Undo', 'Ctrl+Z', ''),
        ),
    ),
    CommandSpec(
        'edit.uppercase', 'UPPERCASE selection', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt>U', 'Ctrl+Alt+U'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for UPPERCASE selection', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'UPPERCASE selection', 'Ctrl+Alt+U', ''),
        ),
    ),
    CommandSpec(
        'file.favourite.add', 'Add to Favourites', menu_path='Favourites',
        shortcuts=(
            _shortcut('<Control><Alt>B', 'Ctrl+Alt+B'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Add to Favourites', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Favourites', 'Add to Favourites', 'Ctrl+Alt+B', ''),
        ),
    ),
    CommandSpec(
        'file.favourite.edit', 'Edit Favourites', menu_path='Favourites',
        shortcuts=(
            _shortcut('<Control><Shift>D', 'Ctrl+Shift+D'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Edit Favourites', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Favourites', 'Edit Favourites', 'Ctrl+Shift+D', ''),
        ),
    ),
    CommandSpec(
        'file.favourite.open', 'Open Favourite', menu_path='File/Favorites',
        risk_class='low', flags=('parameterized',),
        description='Stable W104 command identity for Open Favourite', parameter_kind='path',
    ),
    CommandSpec(
        'file.favourite.reload', 'Reload Favourites', menu_path='Favourites',
        shortcuts=(
            _shortcut('<Control><Alt>R', 'Ctrl+Alt+R'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Reload Favourites', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Favourites', 'Reload Favourites', 'Ctrl+Alt+R', ''),
        ),
    ),
    CommandSpec(
        'file.new', 'New', menu_path='File',
        shortcuts=(
            _shortcut('<Control>N', 'Ctrl+N'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for New', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'New', 'Ctrl+N', ''),
        ),
    ),
    CommandSpec(
        'file.open', 'Open', menu_path='File',
        shortcuts=(
            _shortcut('<Control>O', 'Ctrl+O'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Open', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Open', 'Ctrl+O', ''),
        ),
    ),
    CommandSpec(
        'file.open-drop', 'Open file by drag-and-drop', menu_path='File',
        risk_class='low', flags=('shortcut-guide', 'parameterized'),
        description='Stable W104 command identity for Open file by drag-and-drop', parameter_kind='path',
        guide_entries=(
            CommandGuideEntry('File', 'Open file by drag-and-drop', 'Drop .txt into window', ''),
        ),
    ),
    CommandSpec(
        'file.print', 'Print', menu_path='File',
        shortcuts=(
            _shortcut('<Control>P', 'Ctrl+P'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Print', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Print', 'Ctrl+P', ''),
        ),
    ),
    CommandSpec(
        'file.print-preview', 'Print Preview', menu_path='File',
        shortcuts=(
            _shortcut('<Control><Shift>P', 'Ctrl+Shift+P'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Print Preview', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Print Preview', 'Ctrl+Shift+P', ''),
        ),
    ),
    CommandSpec(
        'file.quit', 'Quit', menu_path='File',
        shortcuts=(
            _shortcut('<Control>Q', 'Ctrl+Q'),
        ),
        risk_class='low-medium', flags=('shortcut-guide',),
        description='Stable W104 command identity for Quit', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Quit', 'Ctrl+Q', ''),
        ),
    ),
    CommandSpec(
        'file.recent.clear', 'Clear Recent Files', menu_path='File/Recent Files',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Clear Recent Files', parameter_kind='',
    ),
    CommandSpec(
        'file.recent.open', 'Open Recent File', menu_path='File/Recent Files',
        risk_class='low', flags=('parameterized',),
        description='Stable W104 command identity for Open Recent File', parameter_kind='path',
    ),
    CommandSpec(
        'file.save', 'Save', menu_path='File',
        shortcuts=(
            _shortcut('<Control>S', 'Ctrl+S'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Save', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Save', 'Ctrl+S', ''),
        ),
    ),
    CommandSpec(
        'file.save-as', 'Save As', menu_path='File',
        shortcuts=(
            _shortcut('<Control><Shift>S', 'Ctrl+Shift+S'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Save As', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Save As', 'Ctrl+Shift+S', ''),
        ),
    ),
    CommandSpec(
        'file.template.manage', 'Manage Templates…', menu_path='File',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Manage Templates…', parameter_kind='',
    ),
    CommandSpec(
        'file.template.open', 'New from Template', menu_path='File/New from Template',
        risk_class='low', flags=('shortcut-guide', 'parameterized'),
        description='Stable W104 command identity for New from Template', parameter_kind='path',
        guide_entries=(
            CommandGuideEntry('File', 'New from Template', 'menu', ''),
        ),
    ),
    CommandSpec(
        'file.template.save', 'Save as Template…', menu_path='File',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Save as Template…', parameter_kind='',
    ),
    CommandSpec(
        'file.workspace.close', 'Close Writing Workspace', menu_path='File',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Close Writing Workspace', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Close Writing Workspace', 'menu', ''),
        ),
    ),
    CommandSpec(
        'file.workspace.duplicate', 'Duplicate Selected Text File', menu_path='File/Writing Workspace',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Duplicate Selected Text File', parameter_kind='',
    ),
    CommandSpec(
        'file.workspace.new-folder', 'New Folder…', menu_path='File/Writing Workspace',
        risk_class='low', flags=(),
        description='Stable W104 command identity for New Folder…', parameter_kind='',
    ),
    CommandSpec(
        'file.workspace.new-text-file', 'New Text File…', menu_path='File/Writing Workspace',
        risk_class='low', flags=(),
        description='Stable W104 command identity for New Text File…', parameter_kind='',
    ),
    CommandSpec(
        'file.workspace.recent.open', 'Recent Workspace', menu_path='File/Writing Workspace/Recent Workspaces',
        risk_class='low', flags=('shortcut-guide', 'parameterized'),
        description='Stable W104 command identity for Recent Workspace', parameter_kind='path',
        guide_entries=(
            CommandGuideEntry('File', 'Recent Workspaces', 'menu', ''),
        ),
    ),
    CommandSpec(
        'file.workspace.refresh', 'Refresh Writing Workspace', menu_path='File',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Refresh Writing Workspace', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Refresh Writing Workspace', 'menu', ''),
        ),
    ),
    CommandSpec(
        'file.workspace.rename', 'Rename Selected Item…', menu_path='File/Writing Workspace',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Rename Selected Item…', parameter_kind='',
    ),
    CommandSpec(
        'file.workspace.reveal', 'Reveal Writing Workspace in File Manager', menu_path='File',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Reveal Writing Workspace in File Manager', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Reveal Writing Workspace in File Manager', 'menu', ''),
        ),
    ),
    CommandSpec(
        'file.workspace.select-folder', 'Select Writing Workspace Folder', menu_path='File',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Select Writing Workspace Folder', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('File', 'Select Writing Workspace Folder', 'menu', ''),
        ),
    ),
    CommandSpec(
        'file.workspace.show-panel', 'Show Workspace Panel', menu_path='File/Writing Workspace',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Show Workspace Panel', parameter_kind='',
    ),
    CommandSpec(
        'file.workspace.trash', 'Move Selected Item to Trash', menu_path='File/Writing Workspace',
        risk_class='medium-high', flags=(),
        description='Stable W104 command identity for Move Selected Item to Trash', parameter_kind='',
    ),
    CommandSpec(
        'help.about', 'About', menu_path='Help',
        shortcuts=(
            _shortcut('F1', 'F1'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for About', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Help', 'About', 'F1', ''),
        ),
    ),
    CommandSpec(
        'help.keyboard-shortcuts', 'Keyboard Shortcuts', menu_path='Help',
        shortcuts=(
            _shortcut('<Control>slash', 'Ctrl+/'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Keyboard Shortcuts', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Help', 'Keyboard Shortcuts', 'Ctrl+/', ''),
        ),
    ),
    CommandSpec(
        'help.user-guide', 'User Guide', menu_path='Help',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for User Guide', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Help', 'User Guide', 'menu', ''),
        ),
    ),
    CommandSpec(
        'navigate.bookmark.manage', 'Manage Bookmarks', menu_path='Navigate',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Manage Bookmarks', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Manage Bookmarks', 'menu', ''),
        ),
    ),
    CommandSpec(
        'navigate.bookmark.next', 'Next Bookmark', menu_path='Navigate',
        shortcuts=(
            _shortcut('F2', 'F2'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Next Bookmark', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Next Bookmark', 'F2', ''),
        ),
    ),
    CommandSpec(
        'navigate.bookmark.previous', 'Previous Bookmark', menu_path='Navigate',
        shortcuts=(
            _shortcut('<Shift>F2', 'Shift+F2'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Previous Bookmark', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Previous Bookmark', 'Shift+F2', ''),
        ),
    ),
    CommandSpec(
        'navigate.bookmark.toggle', 'Insert Bookmark Here', menu_path='Navigate',
        shortcuts=(
            _shortcut('<Control>F2', 'Ctrl+F2'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Insert Bookmark Here', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Insert Bookmark Here', 'Ctrl+F2', ''),
        ),
    ),
    CommandSpec(
        'navigate.document-overview', 'Document Overview', menu_path='Navigate',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Document Overview', parameter_kind='',
    ),
    CommandSpec(
        'navigate.go-line', 'Go to Line', menu_path='Navigate',
        shortcuts=(
            _shortcut('<Control>L', 'Ctrl+L'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Go to Line', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Go to Line', 'Ctrl+L', ''),
        ),
    ),
    CommandSpec(
        'navigate.go-section', 'Go to Section', menu_path='Navigate',
        shortcuts=(
            _shortcut('<Control><Shift>L', 'Ctrl+Shift+L'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Go to Section', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Go to Section', 'Ctrl+Shift+L', ''),
        ),
    ),
    CommandSpec(
        'navigate.heading.next', 'Next Heading', menu_path='Navigate',
        shortcuts=(
            _shortcut('<Control>Page_Down', 'Ctrl+PageDown'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Next Heading', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Next Heading', 'Ctrl+PageDown', ''),
        ),
    ),
    CommandSpec(
        'navigate.heading.previous', 'Previous Heading', menu_path='Navigate',
        shortcuts=(
            _shortcut('<Control>Page_Up', 'Ctrl+PageUp'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Previous Heading', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Previous Heading', 'Ctrl+PageUp', ''),
        ),
    ),
    CommandSpec(
        'navigate.navigator-panel', 'Navigator Panel', menu_path='Navigate',
        shortcuts=(
            _shortcut('<Control><Alt>N', 'Ctrl+Alt+N'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Navigator Panel', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Navigator Panel', 'Ctrl+Alt+N', ''),
        ),
    ),
    CommandSpec(
        'navigate.workspace-panel', 'Writing Workspace', menu_path='Navigate',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Writing Workspace', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Navigate', 'Writing Workspace', 'menu', ''),
        ),
    ),
    CommandSpec(
        'options.always-on-top', 'Always on Top', menu_path='Options',
        shortcuts=(
            _shortcut('<Control><Shift>A', 'Ctrl+Shift+A'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Always on Top', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Options', 'Always on Top', 'Ctrl+Shift+A', ''),
        ),
    ),
    CommandSpec(
        'options.appearance.dark', 'Dark Mode', menu_path='Options',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Dark Mode', parameter_kind='',
    ),
    CommandSpec(
        'options.appearance.light', 'White Background', menu_path='Options',
        risk_class='low', flags=(),
        description='Stable W104 command identity for White Background', parameter_kind='',
    ),
    CommandSpec(
        'options.font', 'Font', menu_path='Options',
        shortcuts=(
            _shortcut('<Control><Shift>F', 'Ctrl+Shift+F'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Font', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Options', 'Font', 'Ctrl+Shift+F', ''),
        ),
    ),
    CommandSpec(
        'options.font-size.adjust', 'Adjust Font Size', menu_path='Options',
        shortcuts=(
            _shortcut('<Control>plus', 'Ctrl++', delta=1),
            _shortcut('<Control>minus', 'Ctrl+-', delta=-1),
        ),
        risk_class='low', flags=('shortcut-guide', 'parameterized'),
        description='Stable W104 command identity for Adjust Font Size', parameter_kind='delta',
        guide_entries=(
            CommandGuideEntry('Options', 'Font Bigger', 'Ctrl++', ''),
            CommandGuideEntry('Options', 'Font Smaller', 'Ctrl+-', ''),
        ),
    ),
    CommandSpec(
        'options.line-numbers', 'Line Numbers', menu_path='Options',
        shortcuts=(),
        risk_class='low', flags=(),
        description='Stable W104 command identity for Line Numbers; no default accelerator', parameter_kind='',
        guide_entries=(),
    ),
    CommandSpec(
        'options.opacity.select', 'Opacity Selection…', menu_path='Options/Opacity',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Opacity Selection…', parameter_kind='',
    ),
    CommandSpec(
        'options.opacity.set', 'Set Opacity', menu_path='Options/Opacity',
        risk_class='low', flags=('parameterized',),
        description='Stable W104 command identity for Set Opacity', parameter_kind='percent',
    ),
    CommandSpec(
        'options.transparent-mode', 'Transparent Mode', menu_path='Options',
        shortcuts=(
            _shortcut('<Control><Shift>T', 'Ctrl+Shift+T'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Transparent Mode', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Options', 'Transparent Mode', 'Ctrl+Shift+T', ''),
        ),
    ),
    CommandSpec(
        'options.word-wrap', 'Word Wrap', menu_path='Options',
        shortcuts=(
            _shortcut('<Alt>Z', 'Alt+Z'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Word Wrap', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Options', 'Word Wrap', 'Alt+Z', ''),
        ),
    ),
    CommandSpec(
        'research.authoring-bridge', 'Authoring Bridge', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Authoring Bridge', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Authoring Bridge', 'menu', ''),
        ),
        owner='ResearchPanelRuntime/AuthoringBridgeRuntime', effect='derived-authoring', invalidations=(),
    ),
    CommandSpec(
        'research.bibliography', 'Bibliography', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Bibliography', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Bibliography', 'menu', ''),
        ),
        owner='ResearchPanelRuntime/ReferencePanelRuntime', effect='references', invalidations=(),
    ),
    CommandSpec(
        'research.capture-scratchpad', 'Capture Selection in Scratchpad', menu_path='Research',
        shortcuts=(
            _shortcut('<Control><Alt><Shift>S', 'Ctrl+Alt+Shift+S'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Capture Selection in Scratchpad', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Capture Selection in Scratchpad', 'Ctrl+Alt+Shift+S', ''),
        ),
        owner='ScratchpadRuntime', effect='scratchpad', invalidations=('SCRATCHPAD',),
    ),
    CommandSpec(
        'research.check', 'Research Check…', menu_path='Research',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Research Check…', parameter_kind='',
        owner='ResearchIntegrityRuntime', effect='read-only', invalidations=(),
    ),
    CommandSpec(
        'research.clips', 'Clip Collection', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Clip Collection', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Clip Collection', 'menu', ''),
        ),
        owner='ResearchPanelRuntime/ClipCollectionRuntime', effect='clips', invalidations=(),
    ),
    CommandSpec(
        'research.create-source-note', 'Create Source Note from Selection', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Create Source Note from Selection', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Create Source Note from Selection', 'menu', ''),
        ),
        owner='AuthoringBridgeRuntime/SourceNotePanelRuntime', effect='source-notes', invalidations=('SOURCE_NOTES',),
    ),
    CommandSpec(
        'research.export-apparatus', 'Export Research Apparatus', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Export Research Apparatus', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Export Research Apparatus', 'menu', ''),
        ),
        owner='ResearchExportRuntime', effect='derived-export', invalidations=(),
    ),
    CommandSpec(
        'research.export-bib', 'Export References as BibTeX/BibLaTeX', menu_path='Research',
        risk_class='medium', flags=('shortcut-guide',),
        description='Stable W104 command identity for Export References as BibTeX/BibLaTeX', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Export References as BibTeX/BibLaTeX', 'menu', ''),
        ),
        owner='BibtexRuntime', effect='derived-export', invalidations=(),
    ),
    CommandSpec(
        'research.export-bibliography-markdown', 'Export Bibliography as Markdown…', menu_path='Research',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Export Bibliography as Markdown…', parameter_kind='',
        owner='ReferencePanelRuntime', effect='derived-export', invalidations=(),
    ),
    CommandSpec(
        'research.export-bibliography-text', 'Export Bibliography as Text…', menu_path='Research',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Export Bibliography as Text…', parameter_kind='',
        owner='ReferencePanelRuntime', effect='derived-export', invalidations=(),
    ),
    CommandSpec(
        'research.export-pandoc', 'Export with Pandoc/citeproc', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Export with Pandoc/citeproc', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Export with Pandoc/citeproc', 'menu', ''),
        ),
        owner='PandocExportRuntime', effect='derived-export', invalidations=(),
    ),
    CommandSpec(
        'research.import-bib', 'Import BibTeX/BibLaTeX', menu_path='Research',
        risk_class='medium', flags=('shortcut-guide',),
        description='Stable W104 command identity for Import BibTeX/BibLaTeX', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Import BibTeX/BibLaTeX', 'menu', ''),
        ),
        owner='BibtexRuntime', effect='references', invalidations=('REFERENCES',),
    ),
    CommandSpec(
        'research.insert-clip', 'Insert Clip', menu_path='Research',
        shortcuts=(
            _shortcut('<Control><Alt>K', 'Ctrl+Alt+K'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Insert Clip', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Insert Clip', 'Ctrl+Alt+K', ''),
        ),
        owner='ClipCollectionRuntime', effect='document', invalidations=('DOCUMENT_CONTENT',),
    ),
    CommandSpec(
        'research.insert-clip-slot', 'Insert Clip numeric quick slots 1-9', menu_path='Research',
        shortcuts=(
            _shortcut('<Control><Alt>1', 'Ctrl+Alt+1', number=1),
            _shortcut('<Control><Alt>2', 'Ctrl+Alt+2', number=2),
            _shortcut('<Control><Alt>3', 'Ctrl+Alt+3', number=3),
            _shortcut('<Control><Alt>4', 'Ctrl+Alt+4', number=4),
            _shortcut('<Control><Alt>5', 'Ctrl+Alt+5', number=5),
            _shortcut('<Control><Alt>6', 'Ctrl+Alt+6', number=6),
            _shortcut('<Control><Alt>7', 'Ctrl+Alt+7', number=7),
            _shortcut('<Control><Alt>8', 'Ctrl+Alt+8', number=8),
            _shortcut('<Control><Alt>9', 'Ctrl+Alt+9', number=9),
        ),
        risk_class='low', flags=('shortcut-guide', 'parameterized'),
        description='Stable W104 command identity for Insert Clip numeric quick slots 1-9', parameter_kind='clip-slot',
        guide_entries=(
            CommandGuideEntry('Research', 'Insert Clip numeric quick slots 1-9', 'Ctrl+Alt+1..9', ''),
        ),
    ),
    CommandSpec(
        'research.insert-heading-link', 'Insert Link to Heading', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Insert Link to Heading', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Insert Link to Heading', 'menu', ''),
        ),
        owner='AuthoringBridgeRuntime/App', effect='document', invalidations=('DOCUMENT_CONTENT',),
    ),
    CommandSpec(
        'research.new-scratchpad-section', 'New Scratchpad Entry for Current Section', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for New Scratchpad Entry for Current Section', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'New Scratchpad Entry for Current Section', 'menu', ''),
        ),
        owner='ScratchpadRuntime', effect='scratchpad', invalidations=('SCRATCHPAD',),
    ),
    CommandSpec(
        'research.open-bibliography', 'Open Bibliography File', menu_path='Research',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Open Bibliography File', parameter_kind='',
        owner='ReferencePanelRuntime', effect='external', invalidations=(),
    ),
    CommandSpec(
        'research.open-citation', 'Open Citation in Bibliography', menu_path='Research',
        shortcuts=(
            _shortcut('<Control><Alt><Shift>Q', 'Ctrl+Alt+Shift+Q'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Open Citation in Bibliography', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Open Citation in Bibliography', 'Ctrl+Alt+Shift+Q', ''),
        ),
        owner='CitationController/ReferencePanelRuntime', effect='selection', invalidations=(),
    ),
    CommandSpec(
        'research.panel', 'Research Panel', menu_path='Research',
        shortcuts=(
            _shortcut('<Control><Alt>C', 'Ctrl+Alt+C'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Research Panel', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Research Panel', 'Ctrl+Alt+C', ''),
        ),
        owner='ResearchPanelRuntime', effect='panel', invalidations=(),
    ),
    CommandSpec(
        'research.quick-cite', 'Quick Cite', menu_path='Research',
        shortcuts=(
            _shortcut('<Control><Alt>Q', 'Ctrl+Alt+Q'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Quick Cite', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Quick Cite', 'Ctrl+Alt+Q', ''),
        ),
        owner='CitationController/App', effect='document', invalidations=('DOCUMENT_CONTENT',),
    ),
    CommandSpec(
        'research.reference-sets', 'Reference Sets', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Reference Sets', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Reference Sets', 'menu', ''),
        ),
        owner='ResearchPanelRuntime/ReferenceSetRuntime', effect='reference-sets', invalidations=(),
    ),
    CommandSpec(
        'research.rename-reference-key', 'Rename Reference Key…', menu_path='Research',
        risk_class='medium-high', flags=(),
        description='Stable W104 command identity for Rename Reference Key…', parameter_kind='',
        owner='ResearchIntegrityRuntime', effect='multi-authority', invalidations=('REFERENCES', 'SOURCE_NOTES', 'REFERENCE_SETS', 'DOCUMENT_CONTENT'),
    ),
    CommandSpec(
        'research.scratchpad', 'Scratchpad', menu_path='Research',
        shortcuts=(
            _shortcut('<Control><Alt>S', 'Ctrl+Alt+S'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Scratchpad', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Scratchpad', 'Ctrl+Alt+S', ''),
        ),
        owner='ResearchPanelRuntime/ScratchpadRuntime', effect='scratchpad', invalidations=(),
    ),
    CommandSpec(
        'research.show-scratchpad-section', 'Show Scratchpad for Current Section', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Show Scratchpad for Current Section', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Show Scratchpad for Current Section', 'menu', ''),
        ),
        owner='ResearchPanelRuntime/ScratchpadRuntime', effect='scratchpad', invalidations=(),
    ),
    CommandSpec(
        'research.source-notes', 'Source Notes', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Source Notes', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Source Notes', 'menu', ''),
        ),
        owner='ResearchPanelRuntime/SourceNotePanelRuntime', effect='source-notes', invalidations=(),
    ),
    CommandSpec(
        'research.tag-integrity', 'Tag Integrity', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Tag Integrity', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Tag Integrity', 'menu', ''),
        ),
        owner='TagIntegrityRuntime', effect='multi-authority', invalidations=('REFERENCES', 'SOURCE_NOTES', 'SCRATCHPAD'),
    ),
    CommandSpec(
        'research.tags', 'Tags', menu_path='Research',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Tags', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Research', 'Tags', 'menu', ''),
        ),
        owner='ResearchPanelRuntime/TagsRuntime', effect='derived-tags', invalidations=(),
    ),
    CommandSpec(
        'tools.language', 'Language…', menu_path='Tools',
        risk_class='low', flags=(),
        description='Stable W104 command identity for Language…', parameter_kind='',
    ),
    CommandSpec(
        'tools.spellcheck', 'External Spellcheck', menu_path='Tools',
        shortcuts=(
            _shortcut('F7', 'F7'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for External Spellcheck', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Tools', 'External Spellcheck', 'F7', ''),
        ),
    ),
    CommandSpec(
        'tools.system-info', 'System Info…', menu_path='Tools',
        risk_class='low', flags=(),
        description='Stable W104 command identity for System Info…', parameter_kind='',
    ),
    CommandSpec(
        'view.character-map', 'Character Map', menu_path='View',
        shortcuts=(
            _shortcut('<Control><Alt>F10', 'Ctrl+Alt+F10'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Character Map', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('View', 'Character Map', 'Ctrl+Alt+F10', ''),
        ),
    ),
    CommandSpec(
        'view.clip-wrap-auto', 'Clip panel adjusts editor wrapping', menu_path='View',
        risk_class='low', flags=('shortcut-guide', 'informational'),
        description='Stable W104 command identity for Clip panel adjusts editor wrapping', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('View', 'Clip panel adjusts editor wrapping', 'automatic', ''),
        ),
    ),
    CommandSpec(
        'view.current-line-highlight', 'Highlight Current Line', menu_path='View',
        shortcuts=(
            _shortcut('<Control><Alt>I', 'Ctrl+Alt+I'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Highlight Current Line', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('View', 'Highlight Current Line', 'Ctrl+Alt+I', ''),
        ),
    ),
    CommandSpec(
        'view.distraction-free', 'Distraction-Free Mode', menu_path='View',
        shortcuts=(
            _shortcut('F11', 'F11'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Distraction-Free Mode', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('View', 'Distraction-Free Mode', 'F11', ''),
        ),
    ),
    CommandSpec(
        'view.focus-mode', 'Focus Mode', menu_path='View',
        shortcuts=(
            _shortcut('F9', 'F9'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Focus Mode', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('View', 'Focus Mode', 'F9', ''),
        ),
    ),
    CommandSpec(
        'writing.clean-pdf', 'Clean Selected Text from PDF', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt><Shift>V', 'Ctrl+Alt+Shift+V'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Clean Selected Text from PDF', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Clean Selected Text from PDF', 'Ctrl+Alt+Shift+V', ''),
        ),
    ),
    CommandSpec(
        'writing.insert-date', 'Insert Date', menu_path='Writing',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Insert Date', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Writing', 'Insert Date', 'menu', ''),
        ),
    ),
    CommandSpec(
        'writing.insert-date-time', 'Insert Date and Time', menu_path='Writing',
        shortcuts=(
            _shortcut('<Control><Alt>D', 'Ctrl+Alt+D'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Insert Date and Time', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Writing', 'Insert Date and Time', 'Ctrl+Alt+D', ''),
        ),
    ),
    CommandSpec(
        'writing.insert-time', 'Insert Time', menu_path='Writing',
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Insert Time', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Writing', 'Insert Time', 'menu', ''),
        ),
    ),
    CommandSpec(
        'writing.join-lines', 'Join Lines', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control>J', 'Ctrl+J'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Join Lines', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Join Lines', 'Ctrl+J', ''),
        ),
    ),
    CommandSpec(
        'writing.reflow-paragraph', 'Reflow Paragraph', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt>J', 'Ctrl+Alt+J'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Reflow Paragraph', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Reflow Paragraph', 'Ctrl+Alt+J', ''),
        ),
    ),
    CommandSpec(
        'writing.remove-extra-spaces', 'Remove Extra Spaces', menu_path='Revise',
        risk_class='low', flags=('pure-handler',),
        description='Stable W104 command identity for Remove Extra Spaces', parameter_kind='',
    ),
    CommandSpec(
        'writing.remove-trailing-spaces', 'Remove Trailing Spaces', menu_path='Revise',
        risk_class='low', flags=('pure-handler',),
        description='Stable W104 command identity for Remove Trailing Spaces', parameter_kind='',
    ),
    CommandSpec(
        'writing.sentence-case', 'Sentence case', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt><Shift>Y', 'Ctrl+Alt+Shift+Y'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Sentence case', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Sentence case', 'Ctrl+Alt+Shift+Y', ''),
        ),
    ),
    CommandSpec(
        'writing.smart-typography', 'Smart Typography', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt>M', 'Ctrl+Alt+M'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Smart Typography', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Smart Typography', 'Ctrl+Alt+M', ''),
        ),
    ),
    CommandSpec(
        'writing.sort-lines', 'Sort A-Z', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt>Up', 'Ctrl+Alt+Up', reverse=False),
            _shortcut('<Control><Alt>Down', 'Ctrl+Alt+Down', reverse=True),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide', 'parameterized'),
        description='Stable W104 command identity for Sort A-Z', parameter_kind='sort-direction',
        guide_entries=(
            CommandGuideEntry('Revise', 'Sort A-Z', 'Ctrl+Alt+Up', 'May conflict with some desktop workspace shortcuts.'),
            CommandGuideEntry('Revise', 'Sort Z-A', 'Ctrl+Alt+Down', 'May conflict with some desktop workspace shortcuts.'),
        ),
    ),
    CommandSpec(
        'writing.statistics', 'Document Statistics', menu_path='Tools',
        shortcuts=(
            _shortcut('<Control><Alt>W', 'Ctrl+Alt+W'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Document Statistics', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Tools', 'Document Statistics', 'Ctrl+Alt+W', ''),
        ),
    ),
    CommandSpec(
        'writing.title-case', 'Title Case', menu_path='Revise',
        shortcuts=(
            _shortcut('<Control><Alt>Y', 'Ctrl+Alt+Y'),
        ),
        risk_class='low', flags=('pure-handler', 'shortcut-guide'),
        description='Stable W104 command identity for Title Case', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Revise', 'Title Case', 'Ctrl+Alt+Y', ''),
        ),
    ),
    CommandSpec(
        'writing.typewriter-mode', 'Typewriter Mode', menu_path='Writing',
        shortcuts=(
            _shortcut('<Shift>F9', 'Shift+F9'),
        ),
        risk_class='low', flags=('shortcut-guide',),
        description='Stable W104 command identity for Typewriter Mode', parameter_kind='',
        guide_entries=(
            CommandGuideEntry('Writing', 'Typewriter Mode', 'Shift+F9', ''),
        ),
    ),
)

COMMAND_REGISTRY = CommandRegistry(COMMAND_SPECS)

LOW_RISK_COMMAND_IDS = (
    'edit.lowercase',
    'edit.uppercase',
    'writing.clean-pdf',
    'writing.insert-date-time',
    'writing.join-lines',
    'writing.reflow-paragraph',
    'writing.remove-extra-spaces',
    'writing.remove-trailing-spaces',
    'writing.sentence-case',
    'writing.smart-typography',
    'writing.sort-lines',
    'writing.statistics',
    'writing.title-case',
)
LOW_RISK_COMMANDS = tuple(COMMAND_REGISTRY.require(command_id) for command_id in LOW_RISK_COMMAND_IDS)

def command_specs() -> tuple[CommandSpec, ...]:
    return COMMAND_SPECS


def command_spec(command_id: str) -> CommandSpec:
    return COMMAND_REGISTRY.require(command_id)


def build_command_registry() -> CommandRegistry:
    return CommandRegistry(COMMAND_SPECS)


def low_risk_command_specs() -> tuple[CommandSpec, ...]:
    return LOW_RISK_COMMANDS


def build_low_risk_registry() -> CommandRegistry:
    return CommandRegistry(LOW_RISK_COMMANDS)


def build_pure_command_layer():
    from calamus_command_handlers import pure_handler_for
    from calamus_command_layer import CommandLayer
    layer = CommandLayer(build_command_registry())
    for command_id in LOW_RISK_COMMAND_IDS:
        handler = pure_handler_for(command_id)
        if handler is not None:
            layer.bind_callable(command_id, handler)
    return layer


def shortcut_bindings() -> tuple[tuple[str, str, dict[str, object]], ...]:
    rows = []
    for spec in COMMAND_SPECS:
        for shortcut in spec.shortcuts:
            rows.append((shortcut.accelerator, spec.command_id, shortcut.data()))
    return tuple(rows)


def shortcut_guide_entries() -> tuple[CommandGuideEntry, ...]:
    rows = []
    # Preserve the historical guide ordering, which is encoded per command by
    # an explicit global sequence below rather than by sorted command IDs.
    for command_id, entry_index in GUIDE_ORDER:
        rows.append(COMMAND_REGISTRY.require(command_id).guide_entries[entry_index])
    return tuple(rows)


def research_command_specs() -> tuple[CommandSpec, ...]:
    return tuple(spec for spec in COMMAND_SPECS if spec.command_id.startswith("research.") and spec.owner)

GUIDE_ORDER = (
    ('file.new', 0),
    ('file.template.open', 0),
    ('file.open', 0),
    ('file.workspace.select-folder', 0),
    ('file.workspace.recent.open', 0),
    ('file.workspace.close', 0),
    ('file.workspace.refresh', 0),
    ('file.workspace.reveal', 0),
    ('file.save', 0),
    ('file.save-as', 0),
    ('file.print-preview', 0),
    ('file.print', 0),
    ('file.open-drop', 0),
    ('file.quit', 0),
    ('edit.undo', 0),
    ('edit.redo', 0),
    ('edit.cut', 0),
    ('edit.copy', 0),
    ('edit.paste', 0),
    ('edit.paste-plain', 0),
    ('edit.select-all', 0),
    ('edit.duplicate-line-selection', 0),
    ('edit.find-replace', 0),
    ('edit.find-replace', 1),
    ('edit.replace-all', 0),
    ('edit.find-next', 0),
    ('edit.find-previous', 0),
    ('research.panel', 0),
    ('research.clips', 0),
    ('research.insert-clip', 0),
    ('research.scratchpad', 0),
    ('research.capture-scratchpad', 0),
    ('research.new-scratchpad-section', 0),
    ('research.show-scratchpad-section', 0),
    ('research.bibliography', 0),
    ('research.tags', 0),
    ('research.reference-sets', 0),
    ('research.source-notes', 0),
    ('research.authoring-bridge', 0),
    ('research.create-source-note', 0),
    ('research.insert-heading-link', 0),
    ('research.quick-cite', 0),
    ('research.open-citation', 0),
    ('research.tag-integrity', 0),
    ('research.import-bib', 0),
    ('research.export-bib', 0),
    ('research.export-apparatus', 0),
    ('research.export-pandoc', 0),
    ('navigate.navigator-panel', 0),
    ('navigate.workspace-panel', 0),
    ('navigate.go-line', 0),
    ('navigate.go-section', 0),
    ('navigate.heading.next', 0),
    ('navigate.heading.previous', 0),
    ('edit.uppercase', 0),
    ('edit.lowercase', 0),
    ('writing.title-case', 0),
    ('writing.sentence-case', 0),
    ('writing.typewriter-mode', 0),
    ('writing.insert-date', 0),
    ('writing.insert-time', 0),
    ('writing.insert-date-time', 0),
    ('navigate.bookmark.toggle', 0),
    ('navigate.bookmark.next', 0),
    ('navigate.bookmark.previous', 0),
    ('navigate.bookmark.manage', 0),
    ('edit.paste-clean-pdf', 0),
    ('writing.clean-pdf', 0),
    ('writing.smart-typography', 0),
    ('writing.reflow-paragraph', 0),
    ('writing.join-lines', 0),
    ('writing.sort-lines', 0),
    ('writing.sort-lines', 1),
    ('file.favourite.add', 0),
    ('file.favourite.edit', 0),
    ('file.favourite.reload', 0),
    ('view.focus-mode', 0),
    ('view.distraction-free', 0),
    ('view.current-line-highlight', 0),
    ('research.insert-clip-slot', 0),
    ('view.clip-wrap-auto', 0),
    ('view.character-map', 0),
    ('options.word-wrap', 0),
    ('options.font', 0),
    ('options.transparent-mode', 0),
    ('options.always-on-top', 0),
    ('options.font-size.adjust', 0),
    ('options.font-size.adjust', 1),
    ('tools.spellcheck', 0),
    ('writing.statistics', 0),
    ('help.user-guide', 0),
    ('help.keyboard-shortcuts', 0),
    ('help.about', 0),
)
