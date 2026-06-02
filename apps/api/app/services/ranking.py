from dataclasses import dataclass
from typing import Any


WEIGHTS = {
    "sharpness_score": 0.30,
    "exposure_score": 0.20,
    "face_quality_score": 0.20,
    "aesthetic_score": 0.20,
    "duplicate_penalty": -0.10,
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


def rank_group(photos: list[dict[str, Any]]) -> list[RankedPhoto]:
    ranked = sorted(
        [
            RankedPhoto(
                photo_id=str(photo["id"]),
                score=final_score(photo),
                recommendation="Pick",
                explanation="Recommended because it has the highest overall technical score in this similar-photo group.",
            )
            for photo in photos
        ],
        key=lambda item: item.score,
        reverse=True,
    )

    if len(ranked) <= 1:
        return ranked

    best = ranked[0]
    rest = [
        RankedPhoto(
            photo_id=item.photo_id,
            score=item.score,
            recommendation="Reject" if item.score < best.score - 0.1 else "Maybe",
            explanation=(
                "Rejected because it is visually similar to a stronger image."
                if item.score < best.score - 0.1
                else "Marked as Maybe because it is close to the strongest image in this group."
            ),
        )
        for item in ranked[1:]
    ]
    return [best, *rest]

