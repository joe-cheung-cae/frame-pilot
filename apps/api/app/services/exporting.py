import csv
import shutil
import zipfile
from collections.abc import Iterable
from pathlib import Path


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


def _existing_original_path(photo: dict) -> Path:
    source = Path(photo.get("project_copy_path") or photo["original_path"])
    if not source.is_file():
        raise FileNotFoundError(f"Original file is missing: {source}")
    return source


def write_selection_csv(target: Path, photos: Iterable[dict]) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "filename",
                "original_path",
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
        for photo in photos:
            writer.writerow(
                {
                    "filename": photo.get("filename", ""),
                    "original_path": photo.get("original_path", ""),
                    "capture_time": photo.get("capture_time") or "",
                    "camera_model": photo.get("camera_model") or "",
                    "lens_model": photo.get("lens_model") or "",
                    "focal_length": photo.get("focal_length") or "",
                    "aperture": photo.get("aperture") or "",
                    "shutter_speed": photo.get("shutter_speed") or "",
                    "iso": "" if photo.get("iso") is None else photo.get("iso"),
                    "status": photo.get("user_status", "Unreviewed"),
                    "star_rating": photo.get("star_rating", 0),
                    "group_id": photo.get("group_id") or "",
                    "ai_recommendation": photo.get("ai_recommendation", "Unreviewed"),
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
                    "recommendation_explanation": photo.get("recommendation_explanation", ""),
                    "processing_state": photo.get("processing_state", ""),
                    "processing_error": photo.get("processing_error") or "",
                }
            )
    return target


def copy_selected_files(target_dir: Path, photos: Iterable[dict]) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    for photo in photos:
        source = _existing_original_path(photo)
        shutil.copy2(source, _unique_destination(target_dir, source.name))
    return target_dir


def zip_selected_files(target_zip: Path, photos: Iterable[dict]) -> Path:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for photo in photos:
            source = _existing_original_path(photo)
            archive.write(source, arcname=_unique_archive_name(used_names, source.name))
    return target_zip
