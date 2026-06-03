from dataclasses import dataclass
from typing import Any

WEIGHTS = {
    "sharpness_score": 0.30,
    "exposure_score": 0.20,
    "contrast_score": 0.15,
    "noise_quality_score": 0.10,
    "face_quality_score": 0.15,
    "aesthetic_score": 0.10,
    "duplicate_penalty": -0.10,
}

QUALITY_LABELS = {
    "sharpness_score": "sharpness",
    "exposure_score": "exposure",
    "contrast_score": "contrast",
    "noise_quality_score": "low noise risk",
    "face_quality_score": "experimental face signal quality",
    "aesthetic_score": "aesthetic balance",
}


@dataclass(frozen=True)
class RankedPhoto:
    photo_id: str
    score: float
    recommendation: str
    explanation: str


def final_score(photo: dict[str, Any]) -> float:
    score = sum(_metric_value(photo, field) * weight for field, weight in WEIGHTS.items())
    return round(max(0.0, min(1.0, score)), 4)


def _metric_value(photo: dict[str, Any], field: str) -> float:
    if field == "noise_quality_score":
        if "noise_score" not in photo or photo.get("noise_score") is None:
            return 0.0
        return 1.0 - float(photo.get("noise_score", 0.0) or 0.0)
    return float(photo.get(field, 0.0) or 0.0)


def _strongest_metric(photo: dict[str, Any]) -> str:
    return max(QUALITY_LABELS, key=lambda field: _metric_value(photo, field) * WEIGHTS[field])


def _top_metric_labels(photo: dict[str, Any], limit: int = 3) -> list[str]:
    ranked_fields = sorted(
        QUALITY_LABELS,
        key=lambda field: _metric_value(photo, field) * WEIGHTS[field],
        reverse=True,
    )
    labels = []
    for field in ranked_fields:
        if _metric_value(photo, field) <= 0:
            continue
        label = QUALITY_LABELS[field]
        if label == "experimental face signal quality" and float(photo.get("eye_open_confidence", 0.0) or 0.0) > 0:
            label = "experimental face and open-eye signals"
        labels.append(label)
        if len(labels) >= limit:
            return labels
    return labels


def _weakest_metric(photo: dict[str, Any]) -> str:
    return min(QUALITY_LABELS, key=lambda field: _metric_value(photo, field) * WEIGHTS[field])


def _largest_metric_gap(photo: dict[str, Any], best_photo: dict[str, Any]) -> str:
    return max(
        QUALITY_LABELS,
        key=lambda field: max(0.0, _metric_value(best_photo, field) - _metric_value(photo, field)) * WEIGHTS[field],
    )


def _pick_explanation(photo: dict[str, Any], group_size: int) -> str:
    strongest = _top_metric_labels(photo, limit=3)
    strongest_text = " and ".join(strongest) if strongest else QUALITY_LABELS[_strongest_metric(photo)]
    if group_size <= 1:
        return f"Recommended because it has the strongest {strongest_text} scores among the available quality signals."
    return f"Recommended because it has the highest overall score in this group, led by its {strongest_text} scores."


def _secondary_explanation(
    photo: dict[str, Any],
    best_photo: dict[str, Any],
    recommendation: str,
    score_gap: float,
) -> str:
    weakest_field = _largest_metric_gap(photo, best_photo)
    if _metric_value(best_photo, weakest_field) <= _metric_value(photo, weakest_field):
        weakest_field = _weakest_metric(photo)
    weakest = QUALITY_LABELS[weakest_field]
    has_face_context = photo.get("face_presence") or best_photo.get("face_presence")
    if weakest == "experimental face signal quality" and has_face_context:
        weakest = "experimental face or eye signals"
    if recommendation == "Reject":
        return f"Rejected because it trails the strongest image by {score_gap:.2f}, with weaker {weakest}."
    return f"Marked as Maybe because it is within {score_gap:.2f} of the strongest image, though {weakest} is weaker."


def rank_group(photos: list[dict[str, Any]]) -> list[RankedPhoto]:
    scored = [(photo, final_score(photo)) for photo in photos]
    scored.sort(key=lambda item: item[1], reverse=True)
    ranked = [
        RankedPhoto(
            photo_id=str(photo["id"]),
            score=score,
            recommendation="Pick",
            explanation=_pick_explanation(photo, len(scored)),
        )
        for photo, score in scored
    ]

    if len(ranked) <= 1:
        return ranked

    best = ranked[0]
    best_photo = scored[0][0]
    rest = [
        RankedPhoto(
            photo_id=item.photo_id,
            score=item.score,
            recommendation="Reject" if item.score < best.score - 0.1 else "Maybe",
            explanation=_secondary_explanation(
                scored[index][0],
                best_photo,
                "Reject" if item.score < best.score - 0.1 else "Maybe",
                best.score - item.score,
            ),
        )
        for index, item in enumerate(ranked[1:], start=1)
    ]
    return [best, *rest]
