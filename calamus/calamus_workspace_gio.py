"""Single-mutation GIO adapter for Writing Workspace operation plans."""
from __future__ import annotations

from dataclasses import dataclass
import os

try:
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    HAVE_GIO = True
except Exception:  # Import remains possible in headless/source-only environments.
    Gio = None
    GLib = None
    HAVE_GIO = False

from calamus_workspace_operations import WorkspaceOperationPlan


@dataclass(frozen=True)
class WorkspaceOperationResult:
    success: bool
    path: str
    message: str = ""
    committed: bool = False


class WorkspaceGioAdapter:
    """Execute exactly one already-validated local filesystem mutation."""

    @staticmethod
    def _validated_parent(plan: WorkspaceOperationPlan) -> tuple[str, str] | None:
        """Revalidate root, parent and target-parent identity at commit time."""
        root = os.path.abspath(plan.root)
        parent = os.path.abspath(plan.parent_path)
        target_parent = os.path.abspath(os.path.dirname(plan.target_path))
        try:
            safe = (
                target_parent == parent
                and os.path.isdir(root)
                and not os.path.islink(root)
                and os.path.isdir(parent)
                and not os.path.islink(parent)
                and os.path.commonpath((os.path.realpath(root), os.path.realpath(parent)))
                == os.path.realpath(root)
            )
        except (OSError, TypeError, ValueError):
            safe = False
        return (root, parent) if safe else None

    @staticmethod
    def _target_within_root(root: str, target_path: str) -> bool:
        try:
            return (
                os.path.commonpath((os.path.realpath(root), os.path.realpath(target_path)))
                == os.path.realpath(root)
            )
        except (OSError, TypeError, ValueError):
            return False

    def create_new_text_file(self, plan: WorkspaceOperationPlan) -> WorkspaceOperationResult:
        if not isinstance(plan, WorkspaceOperationPlan):
            raise TypeError("plan must be WorkspaceOperationPlan")
        if plan.kind != "new-text-file":
            raise ValueError(f"unsupported Workspace operation: {plan.kind}")

        validated = self._validated_parent(plan)
        if validated is None:
            return WorkspaceOperationResult(
                False,
                plan.target_path,
                "The destination folder changed or resolves outside the Writing Workspace.",
                False,
            )
        root, _parent = validated

        if not HAVE_GIO:
            return WorkspaceOperationResult(
                False,
                plan.target_path,
                "GIO is unavailable; the text file was not created.",
                False,
            )

        target = Gio.File.new_for_path(plan.target_path)
        stream = None
        committed = False
        try:
            # FileCreateFlags.NONE is exclusive: an existing target is never
            # overwritten. This is the same GIO boundary used by GNOME
            # Commander for an empty text file.
            stream = target.create(Gio.FileCreateFlags.NONE, None)
            stream.close(None)
            stream = None
            committed = True
            info = target.query_info(
                "standard::type,standard::is-symlink",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                None,
            )
            if (
                info.get_is_symlink()
                or info.get_file_type() != Gio.FileType.REGULAR
                or not self._target_within_root(root, plan.target_path)
            ):
                return WorkspaceOperationResult(
                    False,
                    plan.target_path,
                    "The file was created, but its confined regular-file identity could not be verified.",
                    True,
                )
            return WorkspaceOperationResult(True, plan.target_path, committed=True)
        except GLib.Error as exc:
            return WorkspaceOperationResult(
                False,
                plan.target_path,
                (
                    f"The file was created, but final verification failed: {exc.message}"
                    if committed
                    else f"The text file could not be created: {exc.message}"
                ),
                committed,
            )
        finally:
            if stream is not None:
                try:
                    stream.close(None)
                except GLib.Error:
                    pass

    def create_new_folder(self, plan: WorkspaceOperationPlan) -> WorkspaceOperationResult:
        if not isinstance(plan, WorkspaceOperationPlan):
            raise TypeError("plan must be WorkspaceOperationPlan")
        if plan.kind != "new-folder":
            raise ValueError(f"unsupported Workspace operation: {plan.kind}")

        validated = self._validated_parent(plan)
        if validated is None:
            return WorkspaceOperationResult(
                False,
                plan.target_path,
                "The destination folder changed or resolves outside the Writing Workspace.",
                False,
            )
        root, _parent = validated

        if not HAVE_GIO:
            return WorkspaceOperationResult(
                False,
                plan.target_path,
                "GIO is unavailable; the folder was not created.",
                False,
            )

        target = Gio.File.new_for_path(plan.target_path)
        committed = False
        try:
            # One-level, exclusive create. Recursive directory creation is
            # deliberately excluded so a basename cannot acquire path semantics.
            target.make_directory(None)
            committed = True
            info = target.query_info(
                "standard::type,standard::is-symlink",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                None,
            )
            if (
                info.get_is_symlink()
                or info.get_file_type() != Gio.FileType.DIRECTORY
                or not self._target_within_root(root, plan.target_path)
            ):
                return WorkspaceOperationResult(
                    False,
                    plan.target_path,
                    "The folder was created, but its confined directory identity could not be verified.",
                    True,
                )
            return WorkspaceOperationResult(True, plan.target_path, committed=True)
        except GLib.Error as exc:
            return WorkspaceOperationResult(
                False,
                plan.target_path,
                (
                    f"The folder was created, but final verification failed: {exc.message}"
                    if committed
                    else f"The folder could not be created: {exc.message}"
                ),
                committed,
            )
