# FramePilot v2 Performance Baseline

This document records local synthetic smoke results for v2.5 reliability validation. These numbers are not a formal benchmark; they provide a reproducible baseline for checking that large local workflows complete without crashes, failed items, or obvious memory growth.

Command:

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
```

Latest local run: 2026-06-04.

| Count | Status   | Imported | Processed | Failed Items | Groups | Import Seconds | Process Seconds | Export Seconds | Peak RSS MB |
| ----: | -------- | -------: | --------: | -----------: | -----: | -------------: | --------------: | -------------: | ----------: |
|   100 | complete |      100 |       100 |            0 |     55 |          0.526 |           0.366 |          0.085 |      127.66 |
|   500 | complete |      500 |       500 |            0 |    264 |          2.013 |           1.878 |          0.323 |      148.48 |
|  2000 | complete |     2000 |      2000 |            0 |   1037 |          8.458 |          15.139 |          1.160 |      215.31 |

The smoke uses generated local JPEG images and default CSV, ZIP, and folder exports. Each run writes temporary sources, project data, and export artifacts under the selected output directory.

Use the command above for current-machine validation before relying on these timings. Hardware, Python version, filesystem speed, and image dimensions will change the absolute values.

## Browser-Scale Culling Smoke

Command:

```bash
npm run test:e2e -- tests/e2e/local-workflow.spec.ts -g "validates the culling workspace with 2,000 seeded photos" --project=chromium
```

Latest local run: 2026-06-04.

| Seeded Photos | Seeded Groups | First Preview MS | Status Update MS | Filter Switch MS | Load-All MS | Initial DOM Nodes | Loaded DOM Nodes | Reported JS Heap MB |
| ------------: | ------------: | ---------------: | ---------------: | ---------------: | ----------: | ----------------: | ---------------: | ------------------: |
|          2000 |          1000 |              378 |               88 |               55 |         250 |               941 |              915 |               54.17 |

This smoke uses seeded non-private project, photo, and group records through Playwright route mocks. The generated asset route returns the existing tiny synthetic image response, so this validates culling workspace browser behavior rather than import throughput, real-photo decoding, or large preview image transfer cost.

Validated browser actions:

- The culling workspace opened with a 2,000-photo project.
- The first preview image rendered.
- The Picks filter switched after marking one photo.
- A status update persisted through the mocked API route.
- Keyboard group navigation moved from group 1 to group 2.
- Loading all 2,000 photos and all 1,000 groups completed without crashing.

Browser memory caveat: Chromium exposed `performance.memory` during this local Playwright run, but it is a JS heap estimate, not full browser process RSS, image decode memory, GPU memory, or a cross-browser metric. Treat the reported heap as a smoke signal only. Real photo dimensions and browser process memory remain unmeasured.

Current browser-scale conclusion: 2,000-photo culling is acceptable for seeded metadata records and tiny generated assets on this machine. The remaining risk is real-photo browser cost from larger previews, decode memory, and realistic network/file serving behavior.

## Real Browser-Backend Smoke

Command:

```bash
npm run test:e2e:real-browser
```

Opt-in 500-photo command:

```bash
FRAMEPILOT_BROWSER_PERF_COUNT=500 npm run test:e2e:real-browser
```

Opt-in trace command:

```bash
npm run test:e2e:real-browser:trace
```

Latest local run: 2026-06-04.

| Photo Count | Real Backend | Real Import | Real Processing | Real Asset Serving | CSV Export | Project Create MS | Import MS | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Initial DOM Nodes | After Filter DOM Nodes | After Group DOM Nodes | Reported JS Heap MB |
| ----------: | ------------ | ----------- | --------------- | ------------------ | ---------- | ----------------: | --------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ----------------: | ---------------------: | --------------------: | ------------------: |
|         100 | yes          | yes         | yes             | yes                | yes        |               870 |      1328 |       2115 |              840 |               79 |               50 |                  33 |        48 |               621 |                    343 |                   557 |               48.07 |
|         500 | yes          | yes         | yes             | yes                | yes        |               874 |      3939 |       3119 |              827 |               60 |              117 |                  12 |        55 |               839 |                    599 |                   600 |               68.86 |

This smoke generates synthetic JPEG source photos at test time, creates a project with a temporary project data folder, imports the generated files through the frontend and real backend, runs real processing, opens the real culling workspace, waits for a preview served by `/api/assets`, marks one photo as Pick, switches to the Picks filter, navigates to another group, and creates a CSV export.

Default scope: `npm run test:e2e:real-browser` keeps the real browser-backend smoke at 100 generated photos so local E2E stays reasonably fast. The 500-photo workflow is an opt-in local validation target through `FRAMEPILOT_BROWSER_PERF_COUNT=500 npm run test:e2e:real-browser`. A 2,000-photo real browser-backend workflow remains a future/manual target and is intentionally not part of the default E2E path.

Validated real workflow steps:

- Project creation with a local project data folder.
- Import of 100 default or 500 opt-in generated synthetic JPEG files through the real backend.
- Real backend processing and grouping completion with zero failed items.
- Real preview asset serving into the browser culling workspace.
- Pick status update through the real API.
- Picks filter switch in the real workspace.
- Group navigation in the real workspace.
- CSV export readiness with a browser download link.

What remains unverified:

- Real browser-backend runs at 2,000 photos.
- Full-resolution camera JPEG decode, transfer, and browser memory behavior.
- Full browser process RSS, GPU memory, image decode memory, and operating system memory pressure.
- Long review sessions with repeated filter changes, status updates, compare mode, and load-all behavior.

Instrumentation note: Chromium runs now collect `Performance.getMetrics` through Playwright CDP when available. The smoke records `JSHeapUsedSize`, `JSHeapTotalSize`, `Nodes`, `Documents`, `Frames`, `LayoutCount`, `RecalcStyleCount`, `TaskDuration`, `ScriptDuration`, `LayoutDuration`, and `RecalcStyleDuration`; unavailable metrics are recorded as `null` rather than failing the test. The smoke also records a document DOM node count and the browser-exposed `performance.memory` JS heap estimate when available.

Browser memory caveat: the reported heap value comes from Chromium `performance.memory` and is a JS heap estimate only. It is not full browser process memory, decoded image memory, GPU memory, or a cross-browser metric. The DOM node count is a document element count only; it does not measure decoded image memory, GPU resources, offscreen browser internals, or operating system memory pressure.

### Larger Generated JPEG Validation

Command:

```bash
npm run test:e2e:real-browser:large
```

Latest local run: 2026-06-04.

This run used 500 generated non-private JPEG files at 3000x2000 pixels with JPEG quality 88. It used the real backend, real browser import, real backend processing, real `/api/assets` preview serving, and real CSV export creation. The default `npm run test:e2e:real-browser` command still uses 100 generated 160x120 JPEG files at quality 88 so the normal E2E path remains fast.

| Photo Count | Dimensions | JPEG Quality | Real Backend | Real Asset Serving | Image Generation MS | Project Create MS | Import MS | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Initial DOM Nodes | After Filter DOM Nodes | After Group DOM Nodes | Reported JS Heap MB |
| ----------: | ---------- | -----------: | ------------ | ------------------ | ------------------: | ----------------: | --------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ----------------: | ---------------------: | --------------------: | ------------------: |
|         500 | 3000x2000  |           88 | yes          | yes                |                8504 |               870 |     96062 |       2605 |              825 |               90 |               54 |                  22 |        43 |               677 |                    423 |                   427 |               42.63 |

### 1,000-Photo Real Browser-Backend Validation

Commands:

```bash
FRAMEPILOT_BROWSER_PERF_COUNT=1000 npm run test:e2e:real-browser
FRAMEPILOT_BROWSER_PERF_COUNT=1000 FRAMEPILOT_BROWSER_PERF_WIDTH=3000 FRAMEPILOT_BROWSER_PERF_HEIGHT=2000 FRAMEPILOT_BROWSER_PERF_QUALITY=88 npm run test:e2e:real-browser
```

Local run date: 2026-06-04.

Both runs generated non-private JPEG source photos at test time, created a local project through the real frontend, imported through the real FastAPI backend, ran real processing, served real previews through `/api/assets`, updated one Pick status, switched the Picks filter, navigated groups, and created a CSV export.

| Photo Count | Dimensions | JPEG Quality | Result | Real Backend | Real Import | Real Processing | Real Asset Serving | CSV Export | Image Generation MS | Project Create MS | Import MS | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Initial DOM Nodes | After Filter DOM Nodes | After Group DOM Nodes | Reported JS Heap MB |
| ----------: | ---------- | -----------: | ------ | ------------ | ----------- | --------------- | ------------------ | ---------- | ------------------: | ----------------: | --------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ----------------: | ---------------------: | --------------------: | ------------------: |
|        1000 | 160x120    |           88 | pass   | yes          | yes         | yes             | yes                | yes        |                 295 |               874 |     10603 |       5638 |              852 |               99 |               62 |                  10 |        49 |               858 |                    600 |                   525 |               48.07 |
|        1000 | 3000x2000  |           88 | pass   | yes          | yes         | yes             | yes                | yes        |               17132 |               868 |    193075 |       3615 |              831 |               92 |               60 |                   7 |        47 |               842 |                    600 |                   525 |               45.20 |

The 1,000-photo small-image run completed in 26.1 seconds. The 1,000-photo large-image run completed in 3.7 minutes, with browser-visible import wait accounting for 193.075 seconds. Backend import timing was not enabled for these commands, so the import stage is not split into preview generation, scoring, embedding, hashing, and database timing here.

Caveats:

- The benchmark uses generated synthetic JPEGs, not curated real-world camera photo sets.
- The reported heap value comes from Chromium `performance.memory` and is a JS heap estimate only. It is not full browser process RSS, decoded image memory, GPU memory, or operating system memory pressure.
- DOM node counts are document element counts only.
- These opt-in 1,000-photo commands must stay out of default E2E because the large-image run is intentionally slow.
- Long review sessions, compare mode under repeated use, and full-resolution camera JPEG diversity remain unmeasured.

Release-readiness decision: 1,000-photo real browser-backend validation is now acceptable for generated small images and generated 3000x2000 JPEGs on this machine. A 2,000-photo real browser-backend run should not be the next default gate. Attempt it only as an explicit manual benchmark after either a longer local validation window is available or import architecture work reduces the dominant import-stage cost. The current import architecture still needs more work before it can be considered durable across API process exits.

#### Repeated 500-Photo and 1,000-Photo Validation

Commands:

```bash
FRAMEPILOT_BROWSER_PERF_REPEAT=3 npm run test:e2e:real-browser:large
FRAMEPILOT_BROWSER_PERF_COUNT=1000 npm run test:e2e:real-browser
FRAMEPILOT_BROWSER_PERF_COUNT=1000 FRAMEPILOT_BROWSER_PERF_WIDTH=3000 FRAMEPILOT_BROWSER_PERF_HEIGHT=2000 FRAMEPILOT_BROWSER_PERF_QUALITY=88 npm run test:e2e:real-browser
```

Local run date: 2026-06-04.

The first command uses 500 generated non-private JPEG files at 3000x2000 pixels and JPEG quality 88. The second command uses 1,000 generated non-private JPEG files at 160x120 pixels and JPEG quality 88. The third command uses 1,000 generated non-private JPEG files at 3000x2000 pixels and JPEG quality 88. All passing runs used the real backend, real browser import, real backend processing, real `/api/assets` preview serving, and real CSV export creation. The 1,000-photo large-image shape is an opt-in validation target and should not become part of default E2E.

The browser benchmark now supports `FRAMEPILOT_BROWSER_PERF_REPEAT`; the default remains a single run. Repeat runs are emitted as separate serial Playwright tests, and a `real-browser-backend-repeat-summary` console line reports min, max, mean, and median values. Playwright writes generated sources, project data, exports, and optional traces under `test-results/...`; the E2E backend writes `.framepilot-e2e-data`. These locations are ignored by Git.

Repeated 500 large-image run summary:

| Run | Status | Image Generation MS | Project Create MS | Import Wait MS | Backend Import Seconds | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Reported JS Heap MB | Initial DOM Nodes | After Filter DOM Nodes | After Group DOM Nodes |
| --: | ------ | ------------------: | ----------------: | -------------: | ---------------------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ------------------: | ----------------: | ---------------------: | --------------------: |
|   1 | pass   |                8230 |               875 |          94941 |                 94.547 |       2105 |              837 |               86 |               50 |                  21 |        53 |               51.02 |               691 |                    423 |                   427 |
|   2 | pass   |                9013 |               140 |          98466 |                 97.615 |       1390 |              224 |               93 |               54 |                   9 |        43 |               42.63 |               679 |                    423 |                   427 |
|   3 | pass   |                8460 |               106 |          95902 |                 95.281 |       1387 |              225 |               56 |               81 |                   7 |        42 |               42.63 |               677 |                    423 |                   427 |

Repeated 500 large-image dominant import stage breakdown:

| Run | Preview Generation Seconds | Quality Scoring Seconds | Embedding Generation Seconds | Thumbnail Generation Seconds | Image Decode Seconds | DB Commit Seconds |
| --: | -------------------------: | ----------------------: | ---------------------------: | ---------------------------: | -------------------: | ----------------: |
|   1 |                     36.409 |                  33.713 |                       12.767 |                        3.998 |                3.578 |             1.380 |
|   2 |                     37.658 |                  34.869 |                       13.145 |                        3.926 |                3.749 |             1.417 |
|   3 |                     36.996 |                  33.897 |                       12.790 |                        3.840 |                3.640 |             1.386 |

Repeated 500 summary values:

| Metric                          |    Min |      Mean | Median |    Max |
| ------------------------------- | -----: | --------: | -----: | -----: |
| Import wait, browser MS         |  94941 | 96436.333 |  95902 |  98466 |
| Backend import endpoint seconds | 94.547 |    95.814 | 95.281 | 97.615 |
| Preview generation seconds      | 36.409 |    37.021 | 36.996 | 37.658 |
| Quality scoring seconds         | 33.713 |    34.160 | 33.897 | 34.869 |
| Embedding generation seconds    | 12.767 |    12.901 | 12.790 | 13.145 |
| Thumbnail generation seconds    |  3.840 |     3.921 |  3.926 |  3.998 |
| Image decode seconds            |  3.578 |     3.656 |  3.640 |  3.749 |
| DB commit seconds               |  1.380 |     1.394 |  1.386 |  1.417 |

1,000-photo opt-in result:

| Photo Count | Dimensions | JPEG Quality | Status | Real Backend | Real Asset Serving | Backend Import Timing | Image Generation MS | Project Create MS | Import MS | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Reported JS Heap MB | Initial DOM Nodes | After Filter DOM Nodes | After Group DOM Nodes |
| ----------: | ---------- | -----------: | ------ | ------------ | ------------------ | --------------------- | ------------------: | ----------------: | --------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ------------------: | ----------------: | ---------------------: | --------------------: |
|        1000 | 160x120    |           88 | pass   | yes          | yes                | not enabled           |                 295 |               874 |     10603 |       5638 |              852 |               99 |               62 |                  10 |        49 |               48.07 |               858 |                    600 |                   525 |
|        1000 | 3000x2000  |           88 | pass   | yes          | yes                | not enabled           |               17132 |               868 |    193075 |       3615 |              831 |               92 |               60 |                   7 |        47 |               45.20 |               842 |                    600 |                   525 |

The first 1,000-photo run exposed a benchmark assertion that expected all 1,000 records to be represented in the initially loaded culling text. The culling workspace intentionally starts with a 500-photo window for larger projects, so the harness now validates the Pick filter state and the partial-load indicator instead of assuming all records are loaded up front. No product behavior was changed for this fix.

Pass/fail/skipped status:

- 500 large-image repeated validation: passed, 3 of 3 runs.
- 1,000 small-image opt-in validation: passed after the benchmark assertion fix above.
- 1,000 large-image opt-in validation: passed as an explicit slow manual target.

Caveats:

- The benchmark uses generated synthetic JPEGs, not a curated real-photo set.
- Reported JS heap is Chromium `performance.memory` JS heap only, not full browser process memory, decoded image memory, GPU memory, or OS memory pressure.
- DOM node counts are document element counts only.
- Backend import timing was enabled for the repeated 500 large-image command through `FRAMEPILOT_IMPORT_TIMING=1` in the `test:e2e:real-browser:large` script. It was not enabled for either 1,000-photo validation command.
- The first run in a repeat sequence can include cold browser or route-load cost; the dominant backend import stages are the more useful stability signal.

Conclusion: the repeated 500 large-image backend import endpoint varied from 94.547s to 97.615s, about 3.2% around the mean, and the browser import wait varied from 94.941s to 98.466s, about 3.7% around the mean. Dominant import stages were similarly stable and well below the 15% variability threshold. The opt-in 1,000-photo small-image and large-image real browser-backend workflows passed, while the large-image command remains an explicit slow manual target.

Recommended next step: because the 500 large-image baseline is stable and both 1,000-photo generated-image workflows pass, start import architecture and resumable job work before attempting 2,000-photo real browser-backend validation.

Instrumentation note:

- Chromium CDP metrics are collected at the first preview, after the Picks filter, and after group navigation. The latest 500 large-image run recorded initial CDP values including `JSHeapUsedSize=18512844`, `JSHeapTotalSize=27361280`, `Nodes=1246`, `Documents=1`, and `Frames=1`.
- JS heap and DOM counts remain smoke signals only. They do not measure full browser RSS, decoded image memory, GPU memory, or OS memory pressure.
- First preview asset timing is measured by listening for the first `/api/assets/.../previews/...` response during culling workspace render. The latest 500 large-image run recorded status `200`, content length `13256` bytes, and approximate response duration `3.40 ms`. Missing content length or browser timing values are allowed and recorded as unavailable.
- Optional Playwright trace capture is disabled by default. Use `FRAMEPILOT_BROWSER_PERF_TRACE=1 npm run test:e2e:real-browser` for the default smoke, `npm run test:e2e:real-browser:trace` for the script alias, or `npm run test:e2e:real-browser:large:trace` for the large-image trace. The trace is written under Playwright's per-test `test-results` output directory; inspect it with `npx playwright show-trace <trace.zip>`.
- The large-image script enables backend import timing with `FRAMEPILOT_IMPORT_TIMING=1`. The latest browser-visible import wait was `96.062 s`; the backend import endpoint accounted for `95.441 s`. The remaining `0.621 s` includes request/response, browser, and frontend bookkeeping that this benchmark does not split further.
- A 2,000-photo real browser-backend run should wait until after the dominant import stages are optimized, because import/scoring/preview generation is still dominant and current browser measurements do not cover process RSS, decoded image memory, GPU memory, or long-session pressure.

Instrumented 500 large-image backend import breakdown:

| Stage                   | Calls | Seconds | Seconds / Photo |
| ----------------------- | ----: | ------: | --------------: |
| preview_generation      |   500 |  36.726 |        0.073452 |
| quality_scoring         |   500 |  34.064 |        0.068127 |
| embedding_generation    |   500 |  12.884 |        0.025769 |
| thumbnail_generation    |   500 |   3.863 |        0.007726 |
| image_decode            |   500 |   3.648 |        0.007297 |
| perceptual_hash         |   500 |   2.046 |        0.004093 |
| db_commit               |   500 |   1.488 |        0.002976 |
| db_record_create        |   500 |   0.177 |        0.000354 |
| file_copy               |   500 |   0.111 |        0.000221 |
| content_hash            |   500 |   0.088 |        0.000175 |
| image_open              |   500 |   0.060 |        0.000120 |
| file_stat               |   500 |   0.029 |        0.000058 |
| metadata_extraction     |   500 |   0.003 |        0.000005 |
| processing_invalidation |     1 |   0.017 |               - |
| import_endpoint_commit  |     1 |   0.024 |               - |

Current large-image import conclusion: `preview_generation` is now the largest import stage, with `quality_scoring` close behind. File copy, content hashing, database record creation, and database commits are not meaningful bottlenecks in this generated-image run.

#### Scoring Array-Copy Cleanup Attempt

The scoring path was adjusted to avoid one redundant full-image RGB float32 copy during face-signal thresholding and to reuse the luminance mean for exposure and high-frequency scoring. No scoring weights, thresholds, or output fields were intentionally changed.

| Measurement                    |  Before |   After | Result                        |
| ------------------------------ | ------: | ------: | ----------------------------- |
| 3000x2000 scoring microbench   |  0.1213 |  0.1058 | faster by about 13% per image |
| 500-image `quality_scoring`    |  59.459 |  58.594 | faster by 0.865 s             |
| 500-image backend import total | 134.337 | 136.473 | slower by 2.136 s in this run |
| 500-image browser import wait  | 134.890 | 137.473 | slower by 2.583 s in this run |

Conclusion: the cleanup is safe and slightly reduces measured scoring time, but it does not materially improve the full 500 large-image workflow. Treat the total import delta as run-to-run noise and keep the next optimization focused on a larger lever, especially `preview_generation` or a more substantial documented scoring strategy.

#### Preview WebP Encoding Optimization

Preview WebP output now uses Pillow WebP `method=2` instead of the default encoder effort. Preview quality remains `88`, dimensions remain bounded to 1800px on the long edge, and thumbnails keep their previous settings. The tradeoff is slightly larger generated preview cache files for much faster preview encoding.

| Measurement                     |  Before |   After | Result                         |
| ------------------------------- | ------: | ------: | ------------------------------ |
| 3000x2000 derivative microbench |  0.1290 |  0.0884 | faster by about 31% per image  |
| Microbench preview bytes        |  42,662 |  46,610 | about 9% larger synthetic file |
| 500-image `preview_generation`  |  51.738 |  38.076 | faster by 13.662 s             |
| 500-image backend import total  | 136.473 | 121.113 | faster by 15.360 s             |
| 500-image browser import wait   | 137.473 | 121.699 | faster by 15.774 s             |

Conclusion: the preview encoder effort change materially improves the 500 large-image import path while preserving preview dimensions and local-only cache behavior. `quality_scoring` is now the largest remaining import stage in this generated-image benchmark.

#### Quality Scoring Optimization

Quality scoring now uses a scoring-only Pillow image bounded to a 1600px long edge before converting to NumPy. Sharpness, blur, exposure, contrast, noise, and heuristic face signals are computed on that bounded scoring image. Preview generation output, thumbnail output, stored score field names, scoring weights, score ranges, API response shape, and local-only project behavior are unchanged.

Commands:

```bash
.venv/bin/python -m app.devtools.quality_scoring_bench --output /tmp/framepilot-scoring-after --count 30 --width 3000 --height 2000 --quality 88
npm run test:e2e:real-browser:large
```

Local run date: 2026-06-04.

Dataset: 500 generated non-private JPEG files at 3000x2000 pixels with JPEG quality 88 for the browser-backend smoke; 30 generated JPEG files with the same dimensions and quality for the scoring microbench.

| Measurement                                       |  Before |  After | Result                         |
| ------------------------------------------------- | ------: | -----: | ------------------------------ |
| 3000x2000 scoring microbench seconds / image      |  0.1124 | 0.0745 | faster by about 34% per image  |
| Microbench `overall_score` mean absolute delta    |  0.0000 | 0.0021 | small bounded sampling drift   |
| Microbench `overall_score` maximum absolute delta |  0.0000 | 0.0079 | small bounded sampling drift   |
| Microbench face/eye presence changes              |       0 |      0 | no changes in generated sample |
| 500-image `quality_scoring`                       |  57.245 | 34.104 | faster by 23.141 s             |
| 500-image backend import total                    | 121.113 | 96.138 | faster by 24.975 s             |
| 500-image browser import wait                     | 121.699 | 96.632 | faster by 25.067 s             |

Microbench stage summary after optimization:

| Stage                   | Seconds / Image |
| ----------------------- | --------------: |
| scoring_image_array     |        0.037167 |
| face_signals            |        0.014491 |
| exposure_contrast_noise |        0.007798 |
| luminance_conversion    |        0.004497 |
| sharpness_blur          |        0.002940 |

Score behavior and regression summary:

- Output fields, score weights, normalization ranges, recommendation formulas, and API response shape are unchanged.
- The scoring pixel source changed from the full 3000x2000 image to a deterministic 1600px-long-edge scoring image, so exact numeric scores can drift slightly.
- The generated 30-image microbench recorded `overall_score` mean absolute delta `0.002067`, maximum absolute delta `0.0079`, `sharpness_score` maximum absolute delta `0.0285`, and zero face/eye presence changes against the legacy full-resolution calculation.
- Regression tests cover required score fields and ranges, sharp image ranking over blur, exposure penalties, deterministic scoring, PIL scoring without mutating the source image, and no source file modification.

Caveats:

- The benchmark uses generated synthetic JPEGs, not a curated real-photo set.
- Downscaled sharpness can differ from full-resolution Laplacian variance on unusual textures, fine detail, moire, or creative blur.
- Browser heap and DOM measurements remain smoke signals only and do not measure full browser RSS, decoded image memory, GPU memory, or OS memory pressure.
- The 2,000-photo real browser-backend run remains intentionally unattempted in this iteration.

Conclusion: the bounded scoring image materially reduces the dominant `quality_scoring` cost while preserving stored fields and user-facing semantics. The tradeoff is a small, measured numeric drift versus legacy full-resolution scoring.

Recommended next step: treat `preview_generation` as the next import-stage bottleneck, or run a 1,000-photo real browser-backend validation before attempting a 2,000-photo real browser-backend workflow.

#### Preview Generation Optimization

Preview and thumbnail derivative generation now computes the bounded output size and calls Pillow `resize()` directly from the already decoded RGB image. This avoids making a full-resolution `copy()` before downscaling large images. The resize filter remains Pillow BICUBIC with `reducing_gap=2.0`, matching the previous `thumbnail()` path. Preview format, quality, encoder method, and long-edge bound are unchanged.

Commands:

```bash
.venv/bin/python -m app.devtools.derivative_generation_bench --output /tmp/framepilot-derivative-before --count 30 --width 3000 --height 2000 --quality 88
.venv/bin/python -m app.devtools.derivative_generation_bench --output /tmp/framepilot-derivative-after --count 30 --width 3000 --height 2000 --quality 88
npm run test:e2e:real-browser:large
```

Local run date: 2026-06-04.

Dataset: 500 generated non-private JPEG files at 3000x2000 pixels with JPEG quality 88 for the browser-backend smoke; 30 generated JPEG files with the same dimensions and quality for the derivative microbench.

Preview output settings: WebP, long edge bounded to 1800px, quality `88`, Pillow WebP `method=2`. Thumbnail output remains WebP, long edge bounded to 320px, quality `82`.

| Measurement                                     |    Before |     After | Result                       |
| ----------------------------------------------- | --------: | --------: | ---------------------------- |
| 3000x2000 derivative microbench seconds / image |    0.0808 |    0.0800 | faster by about 1% per image |
| Microbench preview resize seconds / image       |    0.0384 |    0.0378 | faster by about 1% per image |
| Microbench thumbnail generation seconds / image |    0.0081 |    0.0076 | faster by about 6% per image |
| Microbench preview bytes mean                   |   11913.9 |   11913.9 | unchanged                    |
| Microbench preview dimensions                   | 1800x1200 | 1800x1200 | unchanged                    |
| 500-image `preview_generation`                  |    36.984 |    36.726 | faster by 0.258 s            |
| 500-image backend import total                  |    95.875 |    95.441 | faster by 0.434 s            |
| 500-image browser import wait                   |    96.427 |    96.062 | faster by 0.365 s            |

Microbench stage summary after optimization:

| Stage                          | Seconds / Image |
| ------------------------------ | --------------: |
| combined_derivative_generation |        0.080029 |
| preview_resize                 |        0.037826 |
| preview_webp_encode            |        0.035395 |
| thumbnail_generation           |        0.007603 |
| image_decode                   |        0.006097 |
| orientation_handling           |        0.000582 |
| rgb_conversion                 |        0.000553 |
| image_open                     |        0.000166 |

Preview byte-size summary:

- Before and after microbench preview bytes were identical for the 30 generated JPEGs: minimum `7736`, maximum `15302`, mean `11913.87`, total `357416`.
- Split-stage preview output and production combined derivative output had matching byte summaries.
- Preview dimensions remained `1800x1200`; thumbnail dimensions remained `320x213`.

Regression summary:

- Added derivative microbench coverage for image open/decode, orientation handling, RGB conversion, preview resize, preview WebP encode, thumbnail generation, combined derivative generation, preview bytes, and derivative dimensions.
- Import regression coverage now verifies thumbnail and preview files are generated, readable by Pillow, bounded by configured long-edge limits, stored separately from the source, and do not modify the external source file content or mtime.
- Added byte-stability coverage proving the optimized helper matches the legacy Pillow `thumbnail()` output for thumbnail and preview WebP derivatives.

Caveats:

- The measured speedup is small and may partly overlap with run-to-run noise.
- The benchmark uses generated synthetic JPEGs, not a curated real-photo set.
- JPEG `draft()` was not introduced because the current import path already works from an EXIF-transposed RGB image shared by scoring, embedding, hashing, thumbnails, and previews.
- Browser heap and DOM measurements remain smoke signals only and do not measure full browser RSS, decoded image memory, GPU memory, or OS memory pressure.
- The 2,000-photo real browser-backend run remains intentionally unattempted in this iteration.

Conclusion: the direct-resize path is safe and preserves preview semantics, output bytes, dimensions, quality, format, and local-only cache behavior. It provides a modest improvement by avoiding full-size derivative copies, but preview generation remains the largest import stage and WebP encode remains a major part of that time.

Recommended next step: run repeated derivative and 500/1,000-photo validations to separate noise from durable gains, then consider moving derivative and scoring work into a resumable import job before attempting a 2,000-photo real browser-backend workflow.

Validated real workflow steps:

- Project creation with a local project data folder.
- Generation of 500 synthetic JPEG files at larger preview-source dimensions.
- Real import and preview generation for all 500 files.
- Real processing and grouping completion with zero failed items.
- First preview render from a real `/api/assets` preview URL.
- Pick status update through the real API.
- Picks filter switch in the real workspace.
- Group navigation in the real workspace.
- CSV export readiness with a browser download link.

Issue exposed and fixed: the first 500-photo 3000x2000 run exceeded the smoke's fixed 120-second import wait after importing 427 of 500 images. The benchmark harness now scales the import and processing wait with the generated image workload while keeping the default small-image command unchanged.

What remains unverified:

- Real browser-backend runs at 2,000 photos.
- Full browser process RSS, decoded image memory, GPU memory, and operating system memory pressure.
- Full-resolution camera JPEG behavior beyond generated synthetic scene content.
- Long review sessions with repeated filter changes, status updates, compare mode, and load-all behavior.

Browser memory caveat: the reported heap value comes from Chromium `performance.memory` and is a JS heap estimate only. It is not full browser process memory, decoded image memory, GPU memory, or a cross-browser metric.

Recommended next performance step: validate the remaining preview WebP encode and quality-scoring costs across repeated 500/1,000-photo runs, then consider moving derivative and scoring work into a truly non-blocking durable import worker before attempting 2,000-photo real browser-backend validation.

## Import Job Progress Iteration

Command:

```bash
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
```

Local run date: 2026-06-04.

This iteration added a queryable `job_type=import` record for each import request, stage/count progress updates, `complete_with_errors` for mixed imports, failed import jobs for all-skipped batches, frontend import-progress visibility, and conservative same-file reuse. The import request is still synchronous and upload-bound; derivative generation, scoring, hashing, and embedding still happen inside the import endpoint.

| Photo Count | Dimensions | JPEG Quality | Import Job | Import MS | Backend Import Seconds | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Reported JS Heap MB |
| ----------: | ---------- | -----------: | ---------- | --------: | ---------------------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ------------------: |
|         100 | 160x120    |           88 | yes        |      1348 |                      - |       2119 |              847 |               85 |               47 |                  32 |        43 |               45.20 |
|         500 | 3000x2000  |           88 | yes        |     97459 |                 96.819 |       2629 |              839 |               79 |               51 |                  21 |        52 |               42.63 |

500 large-image dominant import stage breakdown after import job progress:

| Stage                | Calls | Seconds |
| -------------------- | ----: | ------: |
| preview_generation   |   500 |  36.824 |
| quality_scoring      |   500 |  33.939 |
| embedding_generation |   500 |  12.952 |
| thumbnail_generation |   500 |   3.873 |
| image_decode         |   500 |   3.653 |
| perceptual_hash      |   500 |   2.057 |
| db_commit            |   500 |   1.498 |

Compared with the previous 500 large-image record in this document, browser import wait increased from `96.062 s` to `97.459 s`, and backend import endpoint time increased from `95.441 s` to `96.819 s`. This iteration was expected to improve queryable progress and safe rerun behavior rather than reduce compute time; the timing change is within the repeated 500-image baseline range already recorded above.

Current import architecture conclusion: long imports now have local job visibility and safer same-file rerun behavior, but the request is not fully asynchronous and import jobs are not durable across API process exits. A future architecture slice should split upload registration from derivative/scoring work or introduce a local worker if large real-photo imports need resumable background execution beyond the current FastAPI process.

### Non-Blocking Import Derivative Worker

Commands:

```bash
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
```

Local run date: 2026-06-04.

This iteration split import into a synchronous upload/register phase and an in-process FastAPI `BackgroundTasks` derivative phase. The import endpoint now returns after supported files are copied into the local project, file identity metadata is recorded, `Photo` records are created or safely reused, grouping state is invalidated when needed, and an import job is created. Thumbnail generation, preview generation, metadata extraction, quality scoring, perceptual hashing, and lightweight embedding generation continue in the local API process with a fresh database session. This is not durable across API process exits; a durable worker would be required for restart-safe resume.

| Photo Count | Dimensions | JPEG Quality | Upload/Register Response MS | Background Derivative Completion MS | Total Import Ready MS | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Reported JS Heap MB |
| ----------: | ---------- | -----------: | --------------------------: | ----------------------------------: | --------------------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ------------------: |
|         100 | 160x120    |           88 |                         430 |                                1310 |                  1740 |       2115 |              836 |               81 |               41 |                  30 |        53 |               45.20 |
|         500 | 3000x2000  |           88 |                        2734 |                               96928 |                 99662 |       2598 |              821 |               82 |               56 |                  24 |        49 |               42.63 |

500 large-image upload/register backend timing:

| Stage                   | Calls | Seconds |
| ----------------------- | ----: | ------: |
| db_commit               |   500 |   0.848 |
| file_copy               |   500 |   0.097 |
| db_record_create        |   500 |   0.085 |
| content_hash            |   500 |   0.054 |
| import_endpoint_total   |     1 |   2.369 |
| import_endpoint_commit  |     1 |   0.017 |
| processing_invalidation |     1 |   0.013 |
| file_stat               |   500 |   0.005 |

Interpretation:

- The 500 large-image upload/register response returned in `2.734 s`, compared with the previous synchronous backend import endpoint baseline of `96.819 s`.
- Total time until import-ready remained similar at `99.662 s`, which is expected because this iteration changes responsiveness and progress visibility rather than total image-processing cost.
- The browser showed import progress until the background derivative job completed, then allowed processing and culling to continue.
- The backend timing attached to the import response now covers upload/register work only. Derivative/scoring/hash/embedding stage timing is no longer part of the import response timing payload.
- Generated images were non-private synthetic JPEGs. The 2,000-photo real browser-backend run remains intentionally unattempted in this iteration.

### Import Job Recovery and Retry Iteration

Commands:

```bash
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
```

Local run date: 2026-06-05.

This reliability iteration added import retry for failed and `complete_with_errors` jobs, kept stale import detection query-driven, and exposed retryable import jobs in the import UI. Retry creates a new local import job, reuses existing valid derivatives, regenerates missing derivatives from the local copied original, preserves photo IDs, preserves `user_status`, preserves `star_rating`, and records unrecoverable photos as failed items. FastAPI `BackgroundTasks` remain local in-process work and are still not durable across API process exits.

| Photo Count | Dimensions | JPEG Quality | Upload/Register Response MS | Background Derivative Completion MS | Total Import Ready MS | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Reported JS Heap MB |
| ----------: | ---------- | -----------: | --------------------------: | ----------------------------------: | --------------------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ------------------: |
|         100 | 160x120    |           88 |                         447 |                                1309 |                  1756 |       2110 |              823 |               60 |               72 |                  40 |        44 |               51.02 |
|         500 | 3000x2000  |           88 |                        2471 |                               96061 |                 98532 |       2099 |              826 |               85 |               56 |                  21 |        46 |               51.02 |

500 large-image upload/register backend timing:

| Stage                   | Calls | Seconds |
| ----------------------- | ----: | ------: |
| db_commit               |   500 |   0.756 |
| db_record_create        |   500 |   0.079 |
| file_copy               |   500 |   0.079 |
| content_hash            |   500 |   0.053 |
| import_endpoint_total   |     1 |   2.131 |
| import_endpoint_commit  |     1 |   0.014 |
| processing_invalidation |     1 |   0.013 |
| file_stat               |   500 |   0.004 |

Interpretation:

- The 500 large-image upload/register response stayed in the same range as the previous background-import baseline (`2.471 s` now versus `2.734 s` previously).
- Total import-ready time remained similar (`98.532 s` now versus `99.662 s` previously), which is expected because this iteration improves recovery and retry semantics rather than preview/scoring throughput.
- The retry behavior was verified through backend tests and a mocked browser workflow; the real browser-backend smoke confirms the normal import/progress path still passes.
- A 2,000-photo real browser-backend run remains intentionally unattempted in this iteration.

### Cooperative Import Cancellation Iteration

Commands:

```bash
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
```

Local run date: 2026-06-05.

This job-control iteration added cooperative cancellation for local import derivative jobs. A cancel request persists `cancellation_requested`; the in-process FastAPI `BackgroundTasks` derivative worker checks that flag at photo-level safe checkpoints, marks the job `cancelled`, records `cancelled_at`, preserves completed derivatives, leaves unprocessed photos retryable, and does not delete or modify original files. Cancelled import jobs are retryable through the existing recovery path, which continues to preserve photo IDs, `user_status`, and `star_rating`. FastAPI `BackgroundTasks` remain local in-process work and are still not durable across API process exits; a persistent queue remains deferred.

| Photo Count | Dimensions | JPEG Quality | Upload/Register Response MS | Background Derivative Completion MS | Total Import Ready MS | Process MS | First Preview MS | Status Update MS | Filter Switch MS | Group Navigation MS | Export MS | Reported JS Heap MB |
| ----------: | ---------- | -----------: | --------------------------: | ----------------------------------: | --------------------: | ---------: | ---------------: | ---------------: | ---------------: | ------------------: | --------: | ------------------: |
|         100 | 160x120    |           88 |                         421 |                                1728 |                  1728 |       2096 |              821 |               53 |               72 |                  32 |        42 |               45.20 |
|         500 | 3000x2000  |           88 |                        2489 |                               98397 |                 98397 |       2603 |              825 |               81 |               55 |                  20 |        42 |               51.02 |

500 large-image upload/register backend timing:

| Stage                   | Calls | Seconds |
| ----------------------- | ----: | ------: |
| db_commit               |   500 |   0.780 |
| db_record_create        |   500 |   0.081 |
| file_copy               |   500 |   0.079 |
| content_hash            |   500 |   0.055 |
| import_endpoint_total   |     1 |   2.185 |
| processing_invalidation |     1 |   0.014 |
| import_endpoint_commit  |     1 |   0.013 |
| file_stat               |   500 |   0.004 |

Interpretation:

- The 500 large-image upload/register response stayed in the same range as the previous retry baseline (`2.489 s` now versus `2.471 s` previously).
- Total import-ready time stayed in the same range (`98.397 s` now versus `98.532 s` previously), so cooperative cancellation checks did not introduce a noticeable timing regression in this generated-image run.
- The real browser-backend smoke confirms the normal import/progress/review/export path still passes after adding cancellation controls.
- A 2,000-photo real browser-backend run remains intentionally unattempted in this iteration.
