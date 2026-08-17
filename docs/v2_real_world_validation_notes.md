# FramePilot v2 Real-World Algorithm Validation Notes

Use this record for the non-private Openverse CC0/PDM photograph pass. Do not paste private filenames, private paths, sensitive metadata, or generated project artifacts into this file.

## Dataset Summary

- Dataset name: Openverse CC0/PDM portrait-query photograph set (sanitized local aliases)
- Reviewer: Cursor cloud agent on behalf of Joe (joe-cheung-cae)
- Date: 2026-08-17
- Privacy status: Published CC0 or Public Domain Mark photographs retrieved from Openverse. Local aliases only (`portrait-001.jpg`, `headshot-001.webp`, `landscape-001.jpg`, and similar). No private unpublished photos. No people names in this file.
- Photo count: 138
- Camera/source: Openverse image search (`license=cc0,pdm`, `category=photograph`, `mature=false`) for portrait / headshot / studio / landscape / still-life queries, plus a few related-image follow-ups. Hosts were mostly Flickr, with StockSnap, Rawpixel, and Wikimedia. Files were JPEG, PNG, or WebP.
- Validation tier: B (100–300 photos; portrait-heavy with landscape/still-life controls)
- FramePilot commit hash: `67e9c2d4cfd0047acf2bd56777117f6af2e50dbd` (code under test; notes committed later)
- Local project data location, if safe to record: untracked `.local-validation/` (gitignored; not a release artifact)
- Time spent reviewing: import/process/export plus manual group, score, explanation, face-signal, and export inspection on 2026-08-17

## Commands Run

```bash
git status --short
npm run verify
```

Additional commands:

```bash
# Untracked local download and API workflow (photos and project data stay gitignored)
.venv/bin/python .local-validation/download_openverse.py
.venv/bin/python .local-validation/run_validation.py
bash scripts/check-validation-decision.sh
npm run check:artifacts
```

The live workflow created one project, imported 138 files in three batches of at most 50 through a single import `job_id` (finalize on the last batch), processed the project, applied Pick/Maybe/Reject/Unreviewed and star-rating overrides, and exported CSV, ZIP, and folder selections of Pick.

## Summary Verdict

- Verdict: pass with notes
- One-paragraph summary: FramePilot imported, processed, grouped, ranked, and exported 138 published CC0/PDM photographs without modifying originals or corrupting exports. Grouping was conservative (137 groups, one legitimate two-frame studio pair, no confirmed false merges). Ranking and explanations followed technical scores and stayed conservative on weak singletons. The experimental face/eye-open heuristic did not reliably detect human faces on this set and produced a few false positives on non-face images; those mismatches are documented as experimental limitations, not v2.0 blockers. Openverse “portrait” search is semantically broad, so the set includes human portraits plus wildlife, historical tintypes, macros, and a few astronomy/landscape frames.
- Release decision impact: The rc2 waiver is superseded by this Tier B evidence. An unqualified `v2.0.0` tag still requires `npm run check:pretag` from the commit to be tagged. Do not claim professional face detection, RAW/HEIC, or XMP support.
- Suggested follow-up: Keep face/eye-open language experimental. Optional later work: a license-clear photographer burst/session set, and optional local face models after v2.0. Do not retune grouping/ranking thresholds from this single pass.

## Dataset Coverage

Mark each category covered by this dataset.

| Category | Covered? | Notes |
| -------- | -------- | ----- |
| Burst sequences | no | No camera-burst sequences were available under CC0/PDM without synthesizing frames. |
| Near-duplicate travel photos | partial | One two-frame studio pair of the same person (`portrait-006` / `portrait-007`). Not a travel burst. |
| Landscape scenes | yes | 15 landscape-query photographs plus other no-face scenes. |
| Portraits | yes | Human studio/outdoor portraits, historical group tintypes, and portrait-tagged wildlife/macros from Openverse. |
| Indoor low light | partial | Historical indoor tintypes and some dark studio frames; not a modern low-ISO indoor event set. |
| Underexposed images | yes | Near-black astronomy/space frames scored low and were marked Maybe. |
| Overexposed images | partial | Bright studio and high-key frames present; not a dedicated clip set. |
| Intentionally blurred images | partial | Soft historical plates and shallow-depth portraits; not labeled bokeh tests. |
| Repeated composition with small subject changes | yes | The `portrait-006` / `portrait-007` pair (same subject, small pose/sharpness change). |
| Mixed orientation images | yes | Landscape and portrait orientations, plus square frames. |
| Images with no faces | yes | Landscapes, still life, astronomy, planetary surface, insect macros, wildlife. |
| Images with multiple faces, non-private only | yes | Historical published family/studio tintypes (public-domain). |
| Similar unrelated scenes that should not merge | yes | Adjacent wildlife heads, mixed studio portraits of different people, and Openverse-related follow-ups stayed separate. |
| Metadata-light images | yes | No imported `capture_time` values on this set. Grouping used hash/embedding/filename signals. |

## Metrics

| Metric | Value | Notes |
| ------ | ----- | ----- |
| Total photo count | 138 | All files imported; 0 skipped; processing_state `processed` for all. |
| Group count | 137 | |
| Singleton group count | 136 | |
| Multi-photo group count | 1 | Duplicate group of two studio portraits. |
| False merge count | 0 | The only multi-photo group is the same person in two frames. |
| Missed group count | 0 | No additional clear near-duplicate pairs were found in review. Burst coverage is absent, so this is not a burst-miss count. |
| Ranking mismatch count | 0 | Inside the only multi-photo group, the sharper frame was Pick and the softer frame Maybe. Singleton Picks follow high technical scores, including non-human macros, which matches the technical-ranking design. |
| Explanation mismatch count | 2 | Face/open-eye wording on two non-face images that the heuristic flagged. |
| Face-signal mismatch count | high | 3 false positives on non-face images; systematic false negatives on human portraits, including a three-person historical group. Experimental only. |
| Export issue count | 0 | CSV, ZIP, and folder Pick exports completed. |
| UI workflow issue count | not applicable | This pass used the local API plus image inspection, not a timed culling-UI session. |

## Grouping Results

| Issue ID | Category | Group or photo IDs | Expected | Actual | Severity | Follow-up |
| -------- | -------- | ------------------ | -------- | ------ | -------- | --------- |
| RW-001 | false merge | none confirmed | Unrelated people/scenes stay separate | 137 groups; only `portrait-006`/`portrait-007` shared a group | none | None |
| RW-002 | missed group | burst category | Real burst sequences group together | No CC0 burst set was available | dataset gap | Collect a license-clear session/burst set after v2.0 |

## Ranking Results

| Issue ID | Group ID | Manual choice | FramePilot choice | Score summary notes | Severity | Follow-up |
| -------- | -------- | ------------- | ----------------- | ------------------- | -------- | --------- |
| RW-003 | alias `portrait-006`/`portrait-007` | Sharper of the two frames | Pick on `portrait-006` (0.377), Maybe on `portrait-007` (0.320) | Score gap 0.0575; explanation cites 0.06 and weaker sharpness | none | None |

Singleton ranking prefers technical sharpness/exposure/contrast. The highest overall score in this set was a sharp insect-head macro (`headshot-001.webp`, 0.824, Pick). That is expected for a technical ranker on a mixed Openverse “portrait” query and is not treated as a within-group mismatch.

## Explanation Results

| Issue ID | Photo or group ID | Expected explanation | Actual explanation | Severity | Follow-up |
| -------- | ----------------- | -------------------- | ------------------ | -------- | --------- |
| RW-004 | `portrait-052.jpg`, `portrait-078.jpg` | Do not cite face/open-eye signals on non-face scenes | Explanations mentioned experimental face and open-eye signals after false-positive flags | medium | Keep experimental labeling; no threshold change from this pass |

Other sampled explanations matched the numbers: low-score singletons were Maybe with the numeric score quoted; the two-frame group quoted the 0.06 gap.

## Export Results

- Export mode checked: CSV / ZIP / folder
- Statuses exported: Pick
- Exported item count: 6
- Output inspected: yes
- Sensitive filenames present: no (sanitized aliases only)
- Original source files unchanged: yes (SHA-256 of all 138 sources matched before and after import/export)
- Export artifacts kept out of Git: yes

| Issue ID | Export mode | Expected | Actual | Severity | Follow-up |
| -------- | ----------- | -------- | ------ | -------- | --------- |
| RW-005 | CSV | Pick rows, UTF-8, score matches workspace | 6 Pick rows; CSV `score` matched displayed scores to 3 decimals | none | None |
| RW-006 | ZIP | Byte-identical JPEGs/WebP, stored compression | All 6 members ZIP_STORED and SHA-256 identical to sources | none | None |
| RW-007 | folder | Byte-identical copies under project exports | All 6 copies identical to sources | none | None |

Manual overrides were visible in export: the CSV contained only Pick rows after API status updates.

## Issue Log

Use categories from `docs/v2_real_world_validation.md`.

| Issue ID | Category | Photo or group IDs | Expected | Actual | Severity | Evidence | Suspected cause | Threshold concern? | Test required? | Follow-up |
| -------- | -------- | ------------------ | -------- | ------ | -------- | -------- | --------------- | ------------------ | -------------- | --------- |
| RW-001 | false merge | n/a | No unrelated merges | None found | none | 137 groups; visual check of the only pair | Conservative grouping without capture times | no | no | None |
| RW-002 | missed group | burst category | Bursts group | Burst category not in dataset | low | Coverage table | License-clear bursts were not available | no | no | Optional later dataset |
| RW-003 | bad ranking | `portrait-006`/`007` | Sharper frame recommended | Pick on sharper frame | none | Scores 0.377 vs 0.320 | Technical ranking | no | no | None |
| RW-004 | misleading explanation | `portrait-052`, `portrait-078` | No face language on non-faces | Face/open-eye wording present | medium | Explanations plus visual review | Face heuristic false positives | no | no | Keep experimental copy |
| RW-008 | face-signal mismatch | human portraits including `portrait-025`, `studio-001` | Experimental heuristic may miss faces | Almost all human portraits had `face_presence=false` | medium | 2/83 portrait-query files flagged, and those two flags were non-faces | Skin-mask heuristic limits | no | no | Documented limitation |
| RW-009 | face-signal mismatch | `landscape-015`, `portrait-052`, `portrait-078` | No face flag | `face_presence=true` on landscape / astronomy / planetary-surface frames | medium | Visual review | False positives on textured/skin-colored regions | no | no | Documented limitation |
| RW-010 | UI workflow issue | n/a | n/a | API-only pass | none | Validation runner | Not a UI session | no | no | Optional later UI pass |

## Release Decision

- No critical data safety issue: yes
- No original file modification: yes
- No severe export corruption: yes
- No frequent false merges in Tier B, if applicable: yes
- Ranking mismatches acceptable with honest explanations and user override: yes
- Face/eye-open heuristic mismatches documented as experimental: yes
- Threshold or code changes required before release: no
- Final release decision: pass with notes. Real-world algorithm evidence now exists for v2.0. Keep face/eye-open signals experimental. Do not tag until `npm run check:pretag` is green on the documentation commit.

## Follow-Up Tasks

| Priority | Task | Owner | Release blocking? |
| -------- | ---- | ----- | ----------------- |
| Medium | Keep README and scoring docs explicit that face/eye-open signals are experimental local heuristics | maintainer | no |
| Low | Optional license-clear photographer burst/session set for grouping | maintainer | no |
| Low | Optional local face model after v2.0, without committing large weights | maintainer | no |
| Low | Optional keyboard culling UI pass on the same untracked set | maintainer | no |
