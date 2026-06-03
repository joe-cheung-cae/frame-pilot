from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.ai.embeddings import cosine_similarity


@dataclass(frozen=True)
class SimilarPhotoGroup:
    photo_ids: list[str]
    group_type: str


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _sort_key(photo: dict[str, Any]) -> tuple[str, str]:
    parsed = _parse_time(photo.get("capture_time"))
    return ((parsed.isoformat() if parsed else ""), photo.get("filename", ""))


def group_similar_photos(
    photos: list[dict[str, Any]],
    similarity_threshold: float = 0.96,
    max_time_gap_seconds: int = 30,
) -> list[SimilarPhotoGroup]:
    if not photos:
        return []

    sorted_photos = sorted(photos, key=_sort_key)
    groups: list[list[dict[str, Any]]] = [[sorted_photos[0]]]

    for photo in sorted_photos[1:]:
        previous = groups[-1][-1]
        previous_time = _parse_time(previous.get("capture_time"))
        current_time = _parse_time(photo.get("capture_time"))
        has_time_gap = False
        if previous_time and current_time:
            gap = abs((current_time - previous_time).total_seconds())
            has_time_gap = gap > max_time_gap_seconds

        similarity = cosine_similarity(previous.get("embedding") or [], photo.get("embedding") or [])
        if similarity >= similarity_threshold and not has_time_gap:
            groups[-1].append(photo)
        else:
            groups.append([photo])

    return [
        SimilarPhotoGroup(
            photo_ids=[str(photo["id"]) for photo in group],
            group_type="duplicate" if len(group) > 1 else "single",
        )
        for group in groups
    ]
