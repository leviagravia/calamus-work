"""Recent Workspaces menu projection."""
from __future__ import annotations


def populate_recent_workspaces_menu(menu, paths, callback):
    for child in tuple(menu.get_children()):
        menu.remove(child)
    created = []
    if not paths:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        item = Gtk.MenuItem(label="No recent workspaces")
        item.set_sensitive(False)
        menu.append(item)
        item.show()
        return ()
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    for path in paths:
        item = Gtk.MenuItem(label=path)
        item.connect("activate", lambda _item, selected=path: callback(selected))
        menu.append(item)
        item.show()
        created.append(item)
    return tuple(created)
