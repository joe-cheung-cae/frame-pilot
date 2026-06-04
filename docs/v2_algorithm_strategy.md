# FramePilot v2 Algorithm Strategy

FramePilot v2 uses deterministic, local, explainable algorithms as the baseline. Optional models can be added later only when the deterministic workflow, tests, and file-safety rules are stable.

## Baseline Signals

Each imported JPEG, PNG, or WebP file records local metadata and derived analysis values:

- capture time, camera model, lens model, focal length, aperture, shutter speed, and ISO when available
- dimensions, file size, file mtime, SHA-256 content hash, and source identity
- thumbnail and preview paths
- perceptual hash
- lightweight local embedding approximation
- sharpness, blur risk, exposure, contrast, noise risk, aesthetic balance
- experimental face, face sharpness, eye-open, and face quality signals

Unsupported HEIC and RAW files are skipped with explicit messages until preview extraction is implemented in a later v2.x slice.

## Similarity Grouping

Grouping is intentionally conservative. The current pipeline:

1. Sorts photos by capture time, falling back to filename.
2. Builds candidate windows instead of comparing every photo pair.
3. Requires compatible dimensions, camera model, and focal length when both sides provide those fields.
4. Uses capture-time proximity when available.
5. Falls back to filename sequence proximity when capture time is unavailable.
6. Uses perceptual hash distance when hashes exist.
7. Falls back to local embedding similarity when hashes are unavailable or invalid.
8. Merges matching pairs with union-find.
9. Splits merged groups when their capture-time span exceeds the burst window.

The goal is to group burst-like and near-duplicate frames without over-merging unrelated photos from the same shoot.

## Ranking

Ranking starts from a deterministic weighted score:

- sharpness
- exposure
- contrast
- inverse noise risk
- experimental face quality
- aesthetic balance
- duplicate penalty

The baseline weights are documented in [Scoring](scoring.md). v2 applies small context adjustments:

- Portrait-like frames with experimental face signals weight face quality slightly higher.
- Landscape-like frames without face signals weight sharpness, exposure, and contrast slightly higher.

These adjustments are intentionally modest. They should improve ordering within similar-photo groups without presenting heuristic signals as professional face, eye, or aesthetic models.

## Recommendations And Explanations

The top-ranked photo in a duplicate group receives a `Pick` recommendation. Other photos receive `Maybe` or `Reject` based on score distance from the best candidate. Single-image groups receive `Pick` only when their deterministic score is solid enough; weak singletons receive `Maybe` rather than an automatic rejection.

Explanations should stay conservative and traceable:

- Pick explanations name the strongest contributing signals.
- Maybe and Reject explanations compare against the strongest image and name the weaker signal.
- Experimental face and eye signals must be labeled as experimental when they influence a recommendation.
- Low-confidence single-image groups should avoid aggressive automatic rejection.

User status and star rating always override AI recommendations for export decisions.

## Evaluation Tests

Algorithm changes should add or update deterministic tests for:

- sharp images beating blurry similar images
- underexposed or overexposed images being penalized
- burst-like sequences grouping together
- unrelated images not over-merging across time, filename, metadata, or hash distance
- group confidence matching score gaps
- explanations matching ranking reasons

Use generated synthetic images and small hand-built metadata records. Do not commit private photo datasets.

## Optional Models

Optional local AI models remain deferred. If added later, they must:

- run locally
- be optional downloads or user-provided assets
- avoid committing large model files
- document source, license, size, and expected CPU performance
- preserve deterministic fallback behavior
- keep JPEG, PNG, and WebP workflows stable when models are unavailable
