import csv
import shutil
import zipfile
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from sqlmodel import Session

from app.models.entities import ExportRecord, ProcessingJob, Project, utc_now

STORED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif"}
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
EXPORT_CANCEL_REASON = "Export job was cancelled by user request"
TERMINAL_EXPORT_CANCEL_NOOP = frozenset({"complete", "complete_with_errors", "failed", "cancelled"})

ExportProgressCallback = Callable[[int, int], None]


class ExportCancelled(Exception):
    """Raised at a cooperative export checkpoint when cancellation was requested."""


def remove_partial_export(target: Path, export_root: Path) -> None:
    try:
        resolved_target = target.resolve(strict=True)
        resolved_export_root = export_root.resolve(strict=True)
    except FileNotFoundError:
        return
    if not resolved_target.is_relative_to(resolved_export_root):
        return
    if target.is_symlink():
        target.unlink()
    elif resolved_target.is_dir():
        shutil.rmtree(resolved_target)
    else:
        resolved_target.unlink()


def fail_and_cleanup_export_record(
    session: Session,
    record: ExportRecord,
    reason: str,
    *,
    commit: bool = False,
) -> ExportRecord:
    try:
        from app.services.processing import project_export_root

        project = session.get(Project, record.project_id)
        if project is not None:
            export_root = project_export_root(project)
            remove_partial_export(Path(record.output_path), export_root)
    except Exception:
        pass
    record.status = "failed"
    record.error_message = reason
    record.completed_at = utc_now()
    session.add(record)
    if commit:
        session.commit()
        session.refresh(record)
    return record


def finalize_cancelled_export_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    now = utc_now()
    record = session.get(ExportRecord, job.id)
    if record is not None and record.status == "running":
        fail_and_cleanup_export_record(session, record, EXPORT_CANCEL_REASON, commit=False)
    job.status = "cancelled"
    job.current_step = "cancelled"
    job.cancellation_requested = True
    job.cancelled_at = now
    job.completed_at = now
    job.interrupted_at = None
    job.worker_id = None
    job.heartbeat_at = None
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def request_export_job_cancellation(session: Session, job: ProcessingJob) -> ProcessingJob:
    if job.job_type != "export":
        return job
    if job.status == "interrupted":
        return finalize_cancelled_export_job(session, job)
    if job.status in TERMINAL_EXPORT_CANCEL_NOOP:
        return job
    now = utc_now()
    job.cancellation_requested = True
    job.current_step = "cancellation_requested"
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def sync_export_job(
    session: Session,
    export_id: str,
    *,
    status: str,
    current_step: str,
    processed_items: int | None = None,
    total_items: int | None = None,
    error_message: str | None = None,
    commit: bool = False,
) -> ProcessingJob | None:
    job = session.get(ProcessingJob, export_id)
    if job is None or job.job_type != "export":
        return None
    now = utc_now()
    job.status = status
    job.current_step = current_step
    if processed_items is not None:
        job.processed_items = processed_items
    if total_items is not None:
        job.total_items = total_items
    if job.total_items:
        job.progress_percent = round(min(100.0, (job.processed_items / job.total_items) * 100), 2)
    if error_message is not None:
        job.error_message = error_message
    if status in {"complete", "failed", "cancelled"}:
        job.completed_at = now
        job.worker_id = None
        job.heartbeat_at = None
        job.interrupted_at = None
    if status == "cancelled":
        job.cancellation_requested = True
        job.cancelled_at = now
    job.updated_at = now
    session.add(job)
    if commit:
        session.commit()
        session.refresh(job)
    return job


def _unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / Path(filename).name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 1
    while True:
        next_candidate = directory / f"{stem}-{index}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        index += 1


def _unique_archive_name(used_names: set[str], filename: str) -> str:
    candidate = Path(filename).name
    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    path = Path(candidate)
    index = 1
    while True:
        next_candidate = f"{path.stem}-{index}{path.suffix}"
        if next_candidate not in used_names:
            used_names.add(next_candidate)
            return next_candidate
        index += 1


def _existing_original_path(photo: dict, project_root: Path | None = None) -> Path:
    source = Path(photo.get("project_copy_path") or photo["original_path"])
    try:
        resolved_source = source.resolve(strict=True)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Original file is missing: {source}") from error
    if not resolved_source.is_file():
        raise FileNotFoundError(f"Original file is missing: {source}")
    if project_root is not None:
        originals_root = (project_root / "originals").resolve(strict=True)
        if not resolved_source.is_relative_to(originals_root):
            raise ValueError("Export source file must stay inside the project originals directory")
    return resolved_source


def csv_safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(CSV_FORMULA_PREFIXES):
        return f"'{text}"
    return text


def _as_photo_list(photos: Iterable[dict]) -> list[dict]:
    return list(photos) if not isinstance(photos, list) else photos


def _report_progress(progress_callback: ExportProgressCallback | None, processed: int, total: int) -> None:
    if progress_callback is not None:
        progress_callback(processed, total)


def write_selection_csv(
    target: Path,
    photos: Iterable[dict],
    progress_callback: ExportProgressCallback | None = None,
) -> Path:
    photo_list: Sequence[dict] = _as_photo_list(photos)
    total = len(photo_list)
    _report_progress(progress_callback, 0, total)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "filename",
                "photo_id",
                "original_path",
                "project_copy_path",
                "source_identity",
                "content_hash",
                "file_size",
                "file_mtime",
                "capture_time",
                "camera_model",
                "lens_model",
                "focal_length",
                "aperture",
                "shutter_speed",
                "iso",
                "status",
                "star_rating",
                "group_id",
                "ai_recommendation",
                "score",
                "sharpness_score",
                "exposure_score",
                "contrast_score",
                "face_presence",
                "face_sharpness_score",
                "eye_open_confidence",
                "face_quality_score",
                "width",
                "height",
                "recommendation_explanation",
                "processing_state",
                "processing_error",
            ],
        )
        writer.writeheader()
        for index, photo in enumerate(photo_list, start=1):
            writer.writerow(
                {
                    "filename": csv_safe_cell(photo.get("filename", "")),
                    "photo_id": csv_safe_cell(photo.get("id", "")),
                    "original_path": csv_safe_cell(photo.get("original_path", "")),
                    "project_copy_path": csv_safe_cell(photo.get("project_copy_path") or ""),
                    "source_identity": csv_safe_cell(photo.get("source_identity") or ""),
                    "content_hash": csv_safe_cell(photo.get("content_hash") or ""),
                    "file_size": photo.get("file_size", 0),
                    "file_mtime": "" if photo.get("file_mtime") is None else photo.get("file_mtime"),
                    "capture_time": csv_safe_cell(photo.get("capture_time") or ""),
                    "camera_model": csv_safe_cell(photo.get("camera_model") or ""),
                    "lens_model": csv_safe_cell(photo.get("lens_model") or ""),
                    "focal_length": csv_safe_cell(photo.get("focal_length") or ""),
                    "aperture": csv_safe_cell(photo.get("aperture") or ""),
                    "shutter_speed": csv_safe_cell(photo.get("shutter_speed") or ""),
                    "iso": "" if photo.get("iso") is None else photo.get("iso"),
                    "status": csv_safe_cell(photo.get("user_status", "Unreviewed")),
                    "star_rating": photo.get("star_rating", 0),
                    "group_id": csv_safe_cell(photo.get("group_id") or ""),
                    "ai_recommendation": csv_safe_cell(photo.get("ai_recommendation", "Unreviewed")),
                    "score": f"{float(photo.get('overall_score', 0.0) or 0.0):.3f}",
                    "sharpness_score": f"{float(photo.get('sharpness_score', 0.0) or 0.0):.3f}",
                    "exposure_score": f"{float(photo.get('exposure_score', 0.0) or 0.0):.3f}",
                    "contrast_score": f"{float(photo.get('contrast_score', 0.0) or 0.0):.3f}",
                    "face_presence": str(bool(photo.get("face_presence", False))).lower(),
                    "face_sharpness_score": f"{float(photo.get('face_sharpness_score', 0.0) or 0.0):.3f}",
                    "eye_open_confidence": ""
                    if photo.get("eye_open_confidence") is None
                    else f"{float(photo.get('eye_open_confidence') or 0.0):.3f}",
                    "face_quality_score": f"{float(photo.get('face_quality_score', 0.0) or 0.0):.3f}",
                    "width": photo.get("width", 0),
                    "height": photo.get("height", 0),
                    "recommendation_explanation": csv_safe_cell(photo.get("recommendation_explanation", "")),
                    "processing_state": csv_safe_cell(photo.get("processing_state", "")),
                    "processing_error": csv_safe_cell(photo.get("processing_error") or ""),
                }
            )
            _report_progress(progress_callback, index, total)
    return target


def copy_selected_files(
    target_dir: Path,
    photos: Iterable[dict],
    project_root: Path | None = None,
    progress_callback: ExportProgressCallback | None = None,
) -> Path:
    photo_list: Sequence[dict] = _as_photo_list(photos)
    total = len(photo_list)
    _report_progress(progress_callback, 0, total)
    target_dir.mkdir(parents=True, exist_ok=True)
    for index, photo in enumerate(photo_list, start=1):
        source = _existing_original_path(photo, project_root)
        shutil.copy2(source, _unique_destination(target_dir, source.name))
        _report_progress(progress_callback, index, total)
    return target_dir


def _zip_compression_for(path: Path) -> int:
    if path.suffix.lower() in STORED_IMAGE_EXTENSIONS:
        return zipfile.ZIP_STORED
    return zipfile.ZIP_DEFLATED


def zip_selected_files(
    target_zip: Path,
    photos: Iterable[dict],
    project_root: Path | None = None,
    progress_callback: ExportProgressCallback | None = None,
) -> Path:
    photo_list: Sequence[dict] = _as_photo_list(photos)
    total = len(photo_list)
    _report_progress(progress_callback, 0, total)
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for index, photo in enumerate(photo_list, start=1):
            source = _existing_original_path(photo, project_root)
            archive.write(
                source,
                arcname=_unique_archive_name(used_names, source.name),
                compress_type=_zip_compression_for(source),
            )
            _report_progress(progress_callback, index, total)
    return target_zip
