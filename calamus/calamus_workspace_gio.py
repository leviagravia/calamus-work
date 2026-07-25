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

from calamus_workspace_operations import (
    WorkspaceContentToken, WorkspaceDuplicatePlan, WorkspaceOperationPlan,
    WorkspacePathToken, WorkspaceRenamePlan, WorkspaceTrashPlan,
)


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

    @staticmethod
    def _current_content_token(path: str) -> WorkspaceContentToken | None:
        try:
            stat_result = os.lstat(path)
        except OSError:
            return None
        return WorkspaceContentToken(
            stat_result.st_dev, stat_result.st_ino, stat_result.st_mode,
            stat_result.st_size, stat_result.st_mtime_ns,
        )

    @staticmethod
    def _delete_created_file(
        path: str, expected_token: WorkspaceContentToken | None
    ) -> bool:
        if not os.path.lexists(path):
            return True
        if (
            not HAVE_GIO
            or expected_token is None
            or os.path.islink(path)
            or not os.path.isfile(path)
            or WorkspaceGioAdapter._current_content_token(path) != expected_token
        ):
            return False
        try:
            Gio.File.new_for_path(path).delete(None)
            return not os.path.lexists(path)
        except GLib.Error:
            return False

    def duplicate_text_file(self, plan: WorkspaceDuplicatePlan) -> WorkspaceOperationResult:
        if not isinstance(plan, WorkspaceDuplicatePlan):
            raise TypeError("plan must be WorkspaceDuplicatePlan")
        if plan.kind != "duplicate-text-file":
            raise ValueError(f"unsupported Workspace operation: {plan.kind}")
        if not HAVE_GIO:
            return WorkspaceOperationResult(
                False, plan.target_path, "GIO is unavailable; nothing was duplicated.", False
            )

        validated = self._validated_parent(plan)
        if validated is None:
            return WorkspaceOperationResult(
                False, plan.target_path,
                "The parent folder changed or resolves outside the Writing Workspace.", False,
            )
        root, _parent = validated
        if (
            os.path.islink(plan.source_path)
            or not os.path.isfile(plan.source_path)
            or self._current_content_token(plan.source_path) != plan.source_token
            or not self._target_within_root(root, plan.source_path)
        ):
            return WorkspaceOperationResult(
                False, plan.target_path,
                "The selected text file changed before it could be duplicated.", False,
            )
        if os.path.lexists(plan.target_path):
            return WorkspaceOperationResult(
                False, plan.target_path, "The duplicate destination already exists.", False
            )
        managed_target = plan.target_path + ".source-notes.md"
        if os.path.lexists(managed_target):
            return WorkspaceOperationResult(
                False, plan.target_path,
                "A managed Source Notes sidecar already exists for the duplicate name.", False,
            )
        if plan.companion_source_path is not None:
            if (
                plan.companion_target_path != managed_target
                or plan.companion_token is None
                or os.path.islink(plan.companion_source_path)
                or not os.path.isfile(plan.companion_source_path)
                or self._current_content_token(plan.companion_source_path) != plan.companion_token
            ):
                return WorkspaceOperationResult(
                    False, plan.target_path,
                    "The managed Source Notes sidecar changed before duplication.", False,
                )

        created_primary = False
        created_companion = False
        primary_target_token = None
        companion_target_token = None

        def rollback_failure(message: str) -> WorkspaceOperationResult:
            companion_ok = (not created_companion) or self._delete_created_file(
                plan.companion_target_path or "", companion_target_token
            )
            primary_ok = (not created_primary) or self._delete_created_file(
                plan.target_path, primary_target_token
            )
            rollback_failed = not (primary_ok and companion_ok)
            return WorkspaceOperationResult(
                False, plan.target_path,
                f"{message} Rollback was incomplete." if rollback_failed else message,
                committed=rollback_failed, source_path=plan.source_path,
                companion_path=plan.companion_target_path or "",
                rollback_failed=rollback_failed,
            )

        try:
            source = Gio.File.new_for_path(plan.source_path)
            target = Gio.File.new_for_path(plan.target_path)
            source.copy(target, Gio.FileCopyFlags.NONE, None, None)
            created_primary = True
            primary_target_token = self._current_content_token(plan.target_path)
            info = target.query_info(
                "standard::type,standard::is-symlink",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, None,
            )
            if (
                info.get_is_symlink()
                or info.get_file_type() != Gio.FileType.REGULAR
                or not self._target_within_root(root, plan.target_path)
                or self._current_content_token(plan.source_path) != plan.source_token
            ):
                return rollback_failure(
                    "The duplicated file or source identity could not be verified."
                )

            if plan.companion_source_path is not None:
                assert plan.companion_target_path is not None
                companion_source = Gio.File.new_for_path(plan.companion_source_path)
                companion_target = Gio.File.new_for_path(plan.companion_target_path)
                companion_source.copy(
                    companion_target, Gio.FileCopyFlags.NONE, None, None
                )
                created_companion = True
                companion_target_token = self._current_content_token(
                    plan.companion_target_path
                )
                companion_info = companion_target.query_info(
                    "standard::type,standard::is-symlink",
                    Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, None,
                )
                if (
                    companion_info.get_is_symlink()
                    or companion_info.get_file_type() != Gio.FileType.REGULAR
                    or self._current_content_token(plan.companion_source_path)
                    != plan.companion_token
                ):
                    return rollback_failure(
                        "The duplicated Source Notes companion could not be verified."
                    )

            return WorkspaceOperationResult(
                True, plan.target_path, committed=True, source_path=plan.source_path,
                companion_path=plan.companion_target_path or "",
            )
        except GLib.Error as exc:
            return rollback_failure(f"The text file could not be duplicated: {exc.message}")


    @staticmethod
    def _validated_trash_source(plan: WorkspaceTrashPlan) -> tuple[str, str] | None:
        root = os.path.abspath(plan.root)
        parent = os.path.abspath(plan.parent_path)
        source = os.path.abspath(plan.source_path)
        try:
            safe = (
                source != root
                and os.path.dirname(source) == parent
                and os.path.isdir(root)
                and not os.path.islink(root)
                and os.path.isdir(parent)
                and not os.path.islink(parent)
                and os.path.commonpath((os.path.realpath(root), os.path.realpath(parent)))
                == os.path.realpath(root)
                and os.path.commonpath((root, source)) == root
            )
        except (OSError, TypeError, ValueError):
            safe = False
        return (root, parent) if safe else None

    @staticmethod
    def _trash_capability(file_obj, expected_type) -> tuple[bool, str]:
        try:
            info = file_obj.query_info(
                "standard::type,standard::is-symlink,access::can-trash",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                None,
            )
        except GLib.Error as exc:
            return False, f"Trash capability could not be verified: {exc.message}"
        if info.get_is_symlink() or info.get_file_type() != expected_type:
            return False, "The selected item changed type or became a symbolic link."
        if info.has_attribute("access::can-trash") and not info.get_attribute_boolean(
            "access::can-trash"
        ):
            return False, "The filesystem reports that this item cannot be moved to Trash."
        return True, ""

    def move_to_trash(self, plan: WorkspaceTrashPlan) -> WorkspaceOperationResult:
        """Move one verified item to the system Trash with no delete fallback.

        A managed Source Notes companion is preflighted before the primary item.
        GIO does not provide a cross-item atomic Trash transaction, so the
        primary document is trashed first.  A later companion failure is
        reported as an explicit committed partial result; Calamus never falls
        back to permanent deletion and never hides the partial outcome.
        """
        if not isinstance(plan, WorkspaceTrashPlan):
            raise TypeError("plan must be WorkspaceTrashPlan")
        if plan.kind != "move-to-trash":
            raise ValueError(f"unsupported Workspace operation: {plan.kind}")
        if not HAVE_GIO:
            return WorkspaceOperationResult(
                False, plan.parent_path, "GIO is unavailable; nothing was moved to Trash.", False
            )

        validated = self._validated_trash_source(plan)
        if validated is None:
            return WorkspaceOperationResult(
                False, plan.parent_path,
                "The selected item parent changed or resolves outside the Writing Workspace.",
                False,
            )
        root, parent = validated
        expected_type = Gio.FileType.DIRECTORY if plan.source_is_directory else Gio.FileType.REGULAR
        if (
            os.path.islink(plan.source_path)
            or not self._same_token(plan.source_path, plan.source_token)
            or plan.source_is_directory != os.path.isdir(plan.source_path)
            or not self._target_within_root(root, plan.source_path)
        ):
            return WorkspaceOperationResult(
                False, parent, "The selected item changed before it could be moved to Trash.", False
            )

        source = Gio.File.new_for_path(plan.source_path)
        trashable, message = self._trash_capability(source, expected_type)
        if not trashable:
            return WorkspaceOperationResult(False, parent, message, False)

        companion = None
        if plan.companion_source_path is not None:
            if (
                plan.companion_token is None
                or os.path.islink(plan.companion_source_path)
                or not os.path.isfile(plan.companion_source_path)
                or not self._same_token(plan.companion_source_path, plan.companion_token)
                or not self._target_within_root(root, plan.companion_source_path)
            ):
                return WorkspaceOperationResult(
                    False, parent,
                    "The managed Source Notes sidecar changed before the item could be moved to Trash.",
                    False,
                )
            companion = Gio.File.new_for_path(plan.companion_source_path)
            companion_trashable, companion_message = self._trash_capability(
                companion, Gio.FileType.REGULAR
            )
            if not companion_trashable:
                return WorkspaceOperationResult(False, parent, companion_message, False)

        try:
            if not source.trash(None):
                return WorkspaceOperationResult(
                    False, parent, "The system Trash operation was not accepted.", False
                )
        except GLib.Error as exc:
            return WorkspaceOperationResult(
                False, parent, f"The item could not be moved to Trash: {exc.message}", False
            )

        primary_committed = not os.path.lexists(plan.source_path)
        if not primary_committed:
            return WorkspaceOperationResult(
                False, parent,
                "GIO reported success, but the selected item is still present at its original path.",
                False,
            )

        if companion is not None:
            try:
                companion_ok = bool(companion.trash(None))
            except GLib.Error as exc:
                return WorkspaceOperationResult(
                    False, parent,
                    "The item was moved to Trash, but its managed Source Notes sidecar "
                    f"could not be moved: {exc.message}",
                    True, source_path=plan.source_path,
                    companion_path=plan.companion_source_path or "",
                )
            if not companion_ok or os.path.lexists(plan.companion_source_path):
                return WorkspaceOperationResult(
                    False, parent,
                    "The item was moved to Trash, but its managed Source Notes sidecar remains "
                    "at the original path.",
                    True, source_path=plan.source_path,
                    companion_path=plan.companion_source_path or "",
                )

        return WorkspaceOperationResult(
            True, parent, committed=True, source_path=plan.source_path,
            companion_path=plan.companion_source_path or "",
        )
