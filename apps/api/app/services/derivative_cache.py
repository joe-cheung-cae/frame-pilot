"""Measure and evict local thumbnail/preview derivatives. Originals stay untouched."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, select

from app.models.entities import Photo, ProcessingJob, Project, utc_now
from app.services.jobs import BLOCKING_JOB_STATUSES

DERIVATIVE_DIR_NAMES = ("thumbnails", "previews")


class DerivativeCacheBusyError(RuntimeError):
    """Raised when a blocking job is using derivatives."""


@dataclass(frozen=True, slots=True)
class DerivativeCacheStats:
    derivative_bytes: int
    file_count: int
    project_count: int
    deleted_files: int = 0


def _is_under(path: Path, root: Path) -> bool:
    try:
        return path.resolve().is_relative_to(root.resolve())
    except (OSError, ValueError):
        return False


def _project_root(project: Project) -> Path | None:
    raw = (project.root_path or "").strip()
    if not raw:
        return None
    try:
        root = Path(raw).expanduser().resolve()
    except (OSError, RuntimeError):
        return None
    if not root.is_dir():
        return None
    return root


def _iter_derivative_files(project_root: Path) -> list[Path]:
    files: list[Path] = []
    for name in DERIVATIVE_DIR_NAMES:
        directory = project_root / name
        if not directory.is_dir():
            continue
        if not _is_under(directory, project_root):
            continue
        for candidate in directory.rglob("*"):
            if not candidate.is_file():
                continue
            if not _is_under(candidate, directory):
                continue
            files.append(candidate)
    return files


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def measure_derivative_cache(session: Session) -> DerivativeCacheStats:
    projects = list(session.exec(select(Project)).all())
    total_bytes = 0
    file_count = 0
    used_projects = 0
    for project in projects:
        root = _project_root(project)
        if root is None:
            continue
        files = _iter_derivative_files(root)
        if not files:
            continue
        used_projects += 1
        file_count += len(files)
        total_bytes += sum(_file_size(path) for path in files)
    return DerivativeCacheStats(
        derivative_bytes=total_bytes,
        file_count=file_count,
        project_count=used_projects,
    )


def _has_blocking_job(session: Session) -> bool:
    job = session.exec(select(ProcessingJob).where(ProcessingJob.status.in_(list(BLOCKING_JOB_STATUSES)))).first()
    return job is not None


def clear_derivative_cache(session: Session) -> DerivativeCacheStats:
    if _has_blocking_job(session):
        raise DerivativeCacheBusyError("Cannot clear derivatives while an import or processing job is active")
    deleted = 0
    photos = list(session.exec(select(Photo)).all())
    for photo in photos:
        photo.thumbnail_path = None
        photo.preview_path = None
        photo.updated_at = utc_now()
        session.add(photo)
    for project in session.exec(select(Project)).all():
        root = _project_root(project)
        if root is None:
            continue
        originals = root / "originals"
        for path in _iter_derivative_files(root):
            if originals.exists() and _is_under(path, originals):
                continue
            try:
                path.unlink()
                deleted += 1
            except OSError:
                continue
    session.commit()
    remaining = measure_derivative_cache(session)
    return DerivativeCacheStats(
        derivative_bytes=remaining.derivative_bytes,
        file_count=remaining.file_count,
        project_count=remaining.project_count,
        deleted_files=deleted,
    )
