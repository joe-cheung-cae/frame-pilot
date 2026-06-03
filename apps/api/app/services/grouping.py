import re
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


def _filename_sequence(filename: str | None) -> int | None:
    if not filename:
        return None
    matches = re.findall(r"\d+", filename)
    if not matches:
        return None
    return int(matches[-1])


def _time_gap_seconds(left: dict[str, Any], right: dict[str, Any]) -> float | None:
    left_time = _parse_time(left.get("capture_time"))
    right_time = _parse_time(right.get("capture_time"))
    if not left_time or not right_time:
        return None
    return abs((right_time - left_time).total_seconds())


def _filename_gap(left: dict[str, Any], right: dict[str, Any]) -> int | None:
    left_sequence = _filename_sequence(left.get("filename"))
    right_sequence = _filename_sequence(right.get("filename"))
    if left_sequence is None or right_sequence is None:
        return None
    return abs(right_sequence - left_sequence)


def _metadata_is_compatible(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for key in ("width", "height", "camera_model", "lens_model", "focal_length"):
        left_value = left.get(key)
        right_value = right.get(key)
        if left_value is not None and right_value is not None and left_value != right_value:
            return False
    return True


def _hash_distance(left_hash: str | None, right_hash: str | None) -> int | None:
    if not left_hash or not right_hash:
        return None
    try:
        return (int(left_hash, 16) ^ int(right_hash, 16)).bit_count()
    except ValueError:
        return None


def _is_candidate_pair(
    left: dict[str, Any],
    right: dict[str, Any],
    max_time_gap_seconds: int,
    max_filename_gap: int,
) -> bool:
    if not _metadata_is_compatible(left, right):
        return False

    time_gap = _time_gap_seconds(left, right)
    if time_gap is not None:
        return time_gap <= max_time_gap_seconds

    filename_gap = _filename_gap(left, right)
    if filename_gap is not None:
        return filename_gap <= max_filename_gap

    return True


def _find(parent: list[int], index: int) -> int:
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index


def _union(parent: list[int], left: int, right: int) -> None:
    left_root = _find(parent, left)
    right_root = _find(parent, right)
    if left_root != right_root:
        parent[right_root] = left_root


def _split_group_by_time_span(group: list[dict[str, Any]], max_time_gap_seconds: int) -> list[list[dict[str, Any]]]:
    if len(group) <= 1:
        return [group]

    dated_group = [(photo, _parse_time(photo.get("capture_time"))) for photo in group]
    if any(capture_time is None for _photo, capture_time in dated_group):
        return [group]

    splits: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_start: datetime | None = None

    for photo, capture_time in dated_group:
        if current_start is not None and capture_time is not None:
            span_seconds = abs((capture_time - current_start).total_seconds())
            if span_seconds > max_time_gap_seconds:
                splits.append(current)
                current = []
                current_start = capture_time
        if current_start is None:
            current_start = capture_time
        current.append(photo)

    if current:
        splits.append(current)
    return splits


def group_similar_photos(
    photos: list[dict[str, Any]],
    similarity_threshold: float = 0.96,
    max_time_gap_seconds: int = 30,
    max_filename_gap: int = 3,
    candidate_window_size: int = 8,
    max_hash_distance: int = 8,
) -> list[SimilarPhotoGroup]:
    if not photos:
        return []

    sorted_photos = sorted(photos, key=_sort_key)
    parent = list(range(len(sorted_photos)))

    for left_index, left_photo in enumerate(sorted_photos):
        window_end = min(len(sorted_photos), left_index + candidate_window_size + 1)
        for right_index in range(left_index + 1, window_end):
            right_photo = sorted_photos[right_index]
            if not _is_candidate_pair(left_photo, right_photo, max_time_gap_seconds, max_filename_gap):
                continue
            hash_distance = _hash_distance(left_photo.get("perceptual_hash"), right_photo.get("perceptual_hash"))
            if hash_distance is not None:
                is_similar = hash_distance <= max_hash_distance
            else:
                similarity = cosine_similarity(left_photo.get("embedding") or [], right_photo.get("embedding") or [])
                is_similar = similarity >= similarity_threshold
            if is_similar:
                _union(parent, left_index, right_index)

    grouped_by_root: dict[int, list[dict[str, Any]]] = {}
    for index, photo in enumerate(sorted_photos):
        grouped_by_root.setdefault(_find(parent, index), []).append(photo)

    groups = list(grouped_by_root.values())
    split_groups = []
    for group in groups:
        split_groups.extend(_split_group_by_time_span(group, max_time_gap_seconds))

    return [
        SimilarPhotoGroup(
            photo_ids=[str(photo["id"]) for photo in group],
            group_type="duplicate" if len(group) > 1 else "single",
        )
        for group in split_groups
    ]
