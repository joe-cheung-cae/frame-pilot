from __future__ import annotations

import json
import shutil
from pathlib import Path

from sqlmodel import Session, create_engine, select

from app.core.config import get_settings
from app.core.local_paths import normalize_user_path
from app.core.project_roots import REGISTRY_FILENAME, is_blocked_allowlist_root, registered_roots
from app.models.entities import ExportRecord, Photo, ProcessingJob, Project
from app.services.jobs import BLOCKING_JOB_STATUSES


class DataDirRelocateError(Exception):
    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def _is_under(path: Path, root: Path) -> bool:
    try:
        resolved = path.expanduser().resolve()
        root_resolved = root.expanduser().resolve()
        return resolved == root_resolved or resolved.is_relative_to(root_resolved)
    except (OSError, ValueError):
        return False


def rewrite_stored_path(stored: str | None, old_root: Path, new_root: Path) -> str | None:
    if stored is None:
        return None
    if stored == "":
        return stored
    try:
        current = Path(stored).expanduser().resolve()
        old_resolved = old_root.expanduser().resolve()
        if not (current == old_resolved or current.is_relative_to(old_resolved)):
            return stored
        relative = current.relative_to(old_resolved)
        return str(new_root.expanduser().resolve() / relative)
    except (OSError, ValueError):
        return stored


def _drop_destination_from_copied_registry(dest: Path) -> None:
    registry = dest / REGISTRY_FILENAME
    if not registry.is_file():
        return
    try:
        payload = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return
    if isinstance(payload, dict):
        items = payload.get("roots", [])
    elif isinstance(payload, list):
        items = payload
    else:
        return
    if not isinstance(items, list):
        return
    dest_key = str(dest.resolve())
    kept: list[str] = []
    for item in items:
        if not isinstance(item, str) or not item:
            continue
        try:
            if str(Path(item).expanduser().resolve()) == dest_key:
                continue
        except OSError:
            pass
        kept.append(item)
    registry.write_text(json.dumps({"roots": kept}, indent=2) + "\n", encoding="utf-8")


def _rewrite_destination_db(dest: Path, old_root: Path) -> None:
    db_path = dest / "framepilot.db"
    if not db_path.is_file():
        return
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    try:
        with Session(engine) as session:
            for project in session.exec(select(Project)).all():
                rewritten = rewrite_stored_path(project.root_path, old_root, dest)
                if rewritten is not None:
                    project.root_path = rewritten
                session.add(project)
            for photo in session.exec(select(Photo)).all():
                original = rewrite_stored_path(photo.original_path, old_root, dest)
                if original is not None:
                    photo.original_path = original
                photo.project_copy_path = rewrite_stored_path(photo.project_copy_path, old_root, dest)
                photo.thumbnail_path = rewrite_stored_path(photo.thumbnail_path, old_root, dest)
                photo.preview_path = rewrite_stored_path(photo.preview_path, old_root, dest)
                session.add(photo)
            for export in session.exec(select(ExportRecord)).all():
                rewritten = rewrite_stored_path(export.output_path, old_root, dest)
                if rewritten is not None:
                    export.output_path = rewritten
                session.add(export)
            session.commit()
    finally:
        engine.dispose()


def _clear_destination_contents(dest: Path) -> None:
    for child in dest.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def _resolve_destination(path: str, old_root: Path) -> Path:
    cleaned = normalize_user_path(path)
    candidate = Path(cleaned)
    if not candidate.is_absolute():
        raise DataDirRelocateError("Data directory path must be an absolute local directory")
    try:
        dest = candidate.resolve()
    except OSError as error:
        raise DataDirRelocateError("Data directory path must be a usable local directory") from error
    if is_blocked_allowlist_root(cleaned, dest, old_root):
        raise DataDirRelocateError("Data directory path cannot target a system directory")
    if _is_under(dest, old_root) or _is_under(old_root, dest):
        raise DataDirRelocateError("Data directory path cannot be inside or contain the current data directory")
    registered = {str(root.expanduser().resolve()) for root in registered_roots()}
    if str(dest) not in registered:
        raise DataDirRelocateError("Data directory path must be registered with POST /api/desktop/project-roots")
    if not dest.exists() or not dest.is_dir():
        raise DataDirRelocateError("Data directory path must be a usable local directory")
    try:
        nonempty = any(dest.iterdir())
    except OSError as error:
        raise DataDirRelocateError("Data directory path must be a usable local directory") from error
    if nonempty:
        raise DataDirRelocateError("Data directory path must be an empty directory")
    return dest


def relocate_data_dir(path: str, session: Session) -> Path:
    old_root = get_settings().data_dir.resolve()
    dest = _resolve_destination(path, old_root)
    blocking = session.exec(select(ProcessingJob).where(ProcessingJob.status.in_(list(BLOCKING_JOB_STATUSES)))).first()
    if blocking is not None:
        raise DataDirRelocateError("Cannot change the data directory while a job is running", status_code=409)

    copied = False
    try:
        shutil.copytree(old_root, dest, dirs_exist_ok=True, symlinks=True)
        copied = True
        _rewrite_destination_db(dest, old_root)
        _drop_destination_from_copied_registry(dest)
    except DataDirRelocateError:
        if copied:
            _clear_destination_contents(dest)
        raise
    except OSError as error:
        if copied:
            _clear_destination_contents(dest)
        raise DataDirRelocateError("Data directory path must be a usable local directory") from error
    return dest
