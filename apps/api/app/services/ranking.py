from dataclasses import dataclass
from typing import Any


WEIGHTS = {
    "sharpness_score": 0.30,
    "exposure_score": 0.20,
    "face_quality_score": 0.20,
    "aesthetic_score": 0.20,
    "duplicate_penalty": -0.10,
}

QUALITY_LABELS = {
    "sharpness_score": "sharpness",
    "exposure_score": "exposure",
    "face_quality_score": "face quality",
    "aesthetic_score": "aesthetic balance",
}


@dataclass(frozen=True)
class RankedPhoto:
    photo_id: str
    score: float
    recommendation: str
    explanation: str


def final_score(photo: dict[str, Any]) -> float:
    score = sum(float(photo.get(field, 0.0) or 0.0) * weight for field, weight in WEIGHTS.items())
    return round(max(0.0, min(1.0, score)), 4)


def _metric_value(photo: dict[str, Any], field: str) -> float:
    return float(photo.get(field, 0.0) or 0.0)


def _strongest_metric(photo: dict[str, Any]) -> str:
    return max(QUALITY_LABELS, key=lambda field: _metric_value(photo, field))


def _weakest_metric(photo: dict[str, Any]) -> str:
    return min(QUALITY_LABELS, key=lambda field: _metric_value(photo, field))


def _pick_explanation(photo: dict[str, Any], group_size: int) -> str:
    strongest = QUALITY_LABELS[_strongest_metric(photo)]
    if strongest == "face quality" and float(photo.get("eye_open_confidence", 0.0) or 0.0) > 0:
        strongest = "face quality and open-eye confidence"
    if group_size <= 1:
        return f"Recommended because it has the strongest {strongest} score among the available quality signals."
    return f"Recommended because it has the highest overall score in this group, led by its {strongest} score."


def _secondary_explanation(photo: dict[str, Any], recommendation: str, score_gap: float) -> str:
    weakest = QUALITY_LABELS[_weakest_metric(photo)]
    if weakest == "face quality" and photo.get("face_presence"):
        weakest = "face or eye quality"
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
    rest = [
        RankedPhoto(
            photo_id=item.photo_id,
            score=item.score,
            recommendation="Reject" if item.score < best.score - 0.1 else "Maybe",
            explanation=_secondary_explanation(
                scored[index][0],
                "Reject" if item.score < best.score - 0.1 else "Maybe",
                best.score - item.score,
            ),
        )
        for index, item in enumerate(ranked[1:], start=1)
    ]
    return [best, *rest]
