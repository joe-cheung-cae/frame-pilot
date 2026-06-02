import csv
import shutil
import zipfile
from pathlib import Path
from typing import Iterable


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
            shutil.copy2(source, target_dir / source.name)
    return target_dir


def zip_selected_files(target_zip: Path, photos: Iterable[dict]) -> Path:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for photo in photos:
            source = Path(photo["original_path"])
            if source.exists():
                archive.write(source, arcname=source.name)
    return target_zip

