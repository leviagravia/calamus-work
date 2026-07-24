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

from calamus_workspace_operations import WorkspaceOperationPlan, WorkspacePathToken, WorkspaceRenamePlan


@dataclass(frozen=True)
class WorkspaceOperationResult:
    success: bool
    path: str
    message: str = ""
    committed: bool = False
    source_path: str = ""
    companion_path: str = ""
    rollback_failed: bool = False


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


    @staticmethod
    def _current_token(path: str) -> WorkspacePathToken | None:
        try:
            stat_result = os.lstat(path)
        except OSError:
            return None
        return WorkspacePathToken(stat_result.st_dev, stat_result.st_ino, stat_result.st_mode)

    @staticmethod
    def _same_token(path: str, token: WorkspacePathToken) -> bool:
        return WorkspaceGioAdapter._current_token(path) == token

    @staticmethod
    def _collision_exists(source_path: str, target_path: str) -> bool:
        if not os.path.lexists(target_path):
            return False
        try:
            return not os.path.samefile(source_path, target_path)
        except OSError:
            return True

    def rename_item(self, plan: WorkspaceRenamePlan) -> WorkspaceOperationResult:
        if not isinstance(plan, WorkspaceRenamePlan):
            raise TypeError("plan must be WorkspaceRenamePlan")
        if plan.kind != "rename":
            raise ValueError(f"unsupported Workspace operation: {plan.kind}")
        if not HAVE_GIO:
            return WorkspaceOperationResult(False, plan.target_path, "GIO is unavailable; nothing was renamed.", False)

        validated = self._validated_parent(plan)
        if validated is None:
            return WorkspaceOperationResult(False, plan.target_path, "The parent folder changed or resolves outside the Writing Workspace.", False)
        root, _parent = validated
        if (
            os.path.islink(plan.source_path)
            or not self._same_token(plan.source_path, plan.source_token)
            or plan.source_is_directory != os.path.isdir(plan.source_path)
            or not self._target_within_root(root, plan.source_path)
        ):
            return WorkspaceOperationResult(False, plan.target_path, "The selected item changed before it could be renamed.", False)
        if self._collision_exists(plan.source_path, plan.target_path):
            return WorkspaceOperationResult(False, plan.target_path, "A file or folder with that name already exists.", False)
        if plan.managed_target_path is not None and os.path.lexists(plan.managed_target_path):
            same_managed_file = False
            if plan.companion_source_path is not None:
                try:
                    same_managed_file = os.path.samefile(
                        plan.companion_source_path, plan.managed_target_path
                    )
                except OSError:
                    same_managed_file = False
            if not same_managed_file:
                return WorkspaceOperationResult(
                    False, plan.target_path,
                    "A managed Source Notes sidecar already exists for the destination name.",
                    False,
                )

        companion_moved = False
        companion_new_file = None
        primary_moved = False
        primary_new_file = None

        def rollback_failure(message: str) -> WorkspaceOperationResult:
            primary_residual = primary_moved
            companion_residual = companion_moved
            if primary_moved and primary_new_file is not None:
                try:
                    primary_new_file.set_display_name(plan.source_name, None)
                    primary_residual = False
                except GLib.Error:
                    primary_residual = True
            if companion_moved and companion_new_file is not None:
                try:
                    companion_new_file.set_display_name(
                        os.path.basename(plan.companion_source_path), None
                    )
                    companion_residual = False
                except GLib.Error:
                    companion_residual = True
            rollback_failed = primary_residual or companion_residual
            return WorkspaceOperationResult(
                False, plan.target_path,
                (f"{message} Rollback was incomplete." if rollback_failed else message),
                rollback_failed, source_path=plan.source_path,
                companion_path=plan.companion_target_path or "",
                rollback_failed=rollback_failed,
            )

        if plan.companion_source_path is not None:
            assert plan.companion_target_path is not None
            assert plan.companion_token is not None
            if (
                os.path.islink(plan.companion_source_path)
                or not os.path.isfile(plan.companion_source_path)
                or not self._same_token(plan.companion_source_path, plan.companion_token)
                or self._collision_exists(plan.companion_source_path, plan.companion_target_path)
            ):
                return WorkspaceOperationResult(False, plan.target_path, "The managed Source Notes sidecar changed or its destination already exists.", False)

        try:
            if plan.companion_source_path is not None:
                companion = Gio.File.new_for_path(plan.companion_source_path)
                companion_new_file = companion.set_display_name(
                    os.path.basename(plan.companion_target_path), None
                )
                companion_moved = True

            source = Gio.File.new_for_path(plan.source_path)
            renamed = source.set_display_name(plan.display_name, None)
            primary_new_file = renamed
            primary_moved = True
            renamed_path = renamed.get_path()
            if os.path.abspath(renamed_path or "") != plan.target_path:
                return rollback_failure(
                    "The returned rename destination identity was unexpected."
                )
            expected_type = Gio.FileType.DIRECTORY if plan.source_is_directory else Gio.FileType.REGULAR
            info = renamed.query_info(
                "standard::type,standard::is-symlink",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, None
            )
            if (info.get_is_symlink() or info.get_file_type() != expected_type
                    or not self._target_within_root(root, plan.target_path)):
                return rollback_failure(
                    "The final confined rename identity could not be verified."
                )
            if plan.companion_target_path is not None:
                if not os.path.isfile(plan.companion_target_path) or os.path.islink(plan.companion_target_path):
                    return rollback_failure(
                        "The renamed Source Notes sidecar could not be verified."
                    )
            return WorkspaceOperationResult(
                True, plan.target_path, committed=True, source_path=plan.source_path,
                companion_path=plan.companion_target_path or ""
            )
        except GLib.Error as exc:
            return rollback_failure(f"The item could not be renamed: {exc.message}")
