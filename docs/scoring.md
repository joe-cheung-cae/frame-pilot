# Scoring

The MVP scoring model is deterministic and explainable.

## Technical Scores

- Sharpness: variance of a simple Laplacian kernel over luminance.
- Blur risk: inverse of normalized sharpness.
- Exposure: distance of mean luminance from middle gray.
- Contrast: normalized luminance standard deviation.
- Noise risk: high-frequency luminance deviation estimate.
- Aesthetic: average of exposure and contrast until a dedicated local model is added.
- Face and eye scores: reserved fields, currently defaulted because no face model is bundled.

## Group Ranking

The group ranking formula is:

```text
final_score =
    0.30 * sharpness_score
  + 0.20 * exposure_score
  + 0.20 * face_quality_score
  + 0.20 * aesthetic_score
  - 0.10 * duplicate_penalty
```

The top-ranked photo receives a Pick recommendation. Other photos in the same group receive Maybe or Reject based on their distance from the best score. User decisions always override recommendations.

