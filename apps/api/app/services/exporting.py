import csv
import shutil
import zipfile
from pathlib import Path
from typing import Iterable


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


def write_selection_csv(target: Path, photos: Iterable[dict]) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["filename", "status", "star_rating", "group_id", "score"])
        writer.writeheader()
        for photo in photos:
            writer.writerow(
                {
                    "filename": photo.get("filename", ""),
                    "status": photo.get("user_status", "Unreviewed"),
                    "star_rating": photo.get("star_rating", 0),
                    "group_id": photo.get("group_id") or "",
                    "score": f"{float(photo.get('overall_score', 0.0) or 0.0):.3f}",
                }
            )
    return target


def copy_selected_files(target_dir: Path, photos: Iterable[dict]) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    for photo in photos:
        source = Path(photo["original_path"])
        if source.exists():
            shutil.copy2(source, _unique_destination(target_dir, source.name))
    return target_dir


def zip_selected_files(target_zip: Path, photos: Iterable[dict]) -> Path:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for photo in photos:
            source = Path(photo["original_path"])
            if source.exists():
                archive.write(source, arcname=_unique_archive_name(used_names, source.name))
    return target_zip
