# Scoring

The MVP scoring model is deterministic and explainable.

## Technical Scores

- Sharpness: variance of a simple Laplacian kernel over luminance.
- Blur risk: inverse of normalized sharpness.
- Exposure: distance of mean luminance from middle gray.
- Contrast: normalized luminance standard deviation.
- Noise risk: high-frequency luminance deviation estimate.
- Aesthetic: average of exposure and contrast until a dedicated local model is added.
- Experimental face and eye scores: lightweight local heuristic signals, not a professional face detection model.

## Face And Eye Heuristic

The MVP does not bundle a trained face detector, landmark detector, or eye-state model. Face and eye scoring is implemented as a small deterministic NumPy heuristic so the workflow can expose portrait-aware ranking signals while staying local-first and dependency-light.

The heuristic:

1. Builds a broad skin-tone mask from RGB channel thresholds.
2. Rejects images with too little candidate skin area.
3. Checks the candidate bounding box shape, area, and fill ratio to estimate `face_presence`.
4. Measures `face_sharpness_score` with the same simple Laplacian variance approach used for global sharpness, scoped to the candidate face region.
5. Estimates `eye_open_confidence` from the amount of dark detail in the upper-middle portion of the candidate face box.
6. Combines face sharpness, eye-open confidence, and global sharpness into `face_quality_score`.

These experimental signals are useful as weak MVP ranking hints. They can miss faces, especially with unusual lighting, skin tones, profiles, occlusion, very small faces, heavy color grading, grayscale images, or non-portrait scenes. They can also produce false positives on skin-colored objects. They should not be treated as identity detection, biometric analysis, or a reliable professional portrait quality model.

## Group Ranking

The group ranking formula is:

```text
final_score =
    0.30 * sharpness_score
  + 0.20 * exposure_score
  + 0.15 * contrast_score
  + 0.10 * noise_quality_score
  + 0.15 * experimental_face_quality_score
  + 0.10 * aesthetic_score
  - 0.10 * duplicate_penalty
```

`noise_quality_score` is computed as the inverse of local noise risk. The top-ranked photo receives a Pick recommendation. Other photos in the same group receive Maybe or Reject based on their distance from the best score. User decisions always override recommendations.
