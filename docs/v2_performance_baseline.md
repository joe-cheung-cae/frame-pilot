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
|         500 | 3000x2000  |           88 | yes          | yes                |                8429 |               855 |    121699 |       2612 |              838 |               59 |               88 |                  23 |        44 |               693 |                    423 |                   427 |               42.63 |

Instrumentation note:

- Chromium CDP metrics are collected at the first preview, after the Picks filter, and after group navigation. The latest 500 large-image run recorded initial CDP values including `JSHeapUsedSize=18600508`, `JSHeapTotalSize=27099136`, `Nodes=1262`, `Documents=1`, and `Frames=1`.
- JS heap and DOM counts remain smoke signals only. They do not measure full browser RSS, decoded image memory, GPU memory, or OS memory pressure.
- First preview asset timing is measured by listening for the first `/api/assets/.../previews/...` response during culling workspace render. The latest 500 large-image run recorded status `200`, content length `9212` bytes, and approximate response duration `4.05 ms`. Missing content length or browser timing values are allowed and recorded as unavailable.
- Optional Playwright trace capture is disabled by default. Use `FRAMEPILOT_BROWSER_PERF_TRACE=1 npm run test:e2e:real-browser` for the default smoke, `npm run test:e2e:real-browser:trace` for the script alias, or `npm run test:e2e:real-browser:large:trace` for the large-image trace. The trace is written under Playwright's per-test `test-results` output directory; inspect it with `npx playwright show-trace <trace.zip>`.
- The large-image script enables backend import timing with `FRAMEPILOT_IMPORT_TIMING=1`. The latest browser-visible import wait was `121.699 s`; the backend import endpoint accounted for `121.113 s`. The remaining `0.586 s` includes request/response, browser, and frontend bookkeeping that this benchmark does not split further.
- A 2,000-photo real browser-backend run should wait until after the dominant import stages are optimized, because import/scoring/preview generation is still dominant and current browser measurements do not cover process RSS, decoded image memory, GPU memory, or long-session pressure.

Instrumented 500 large-image backend import breakdown:

| Stage                   | Calls | Seconds | Seconds / Photo |
| ----------------------- | ----: | ------: | --------------: |
| quality_scoring         |   500 |  57.245 |        0.114490 |
| preview_generation      |   500 |  38.076 |        0.076153 |
| embedding_generation    |   500 |  13.255 |        0.026510 |
| thumbnail_generation    |   500 |   4.345 |        0.008691 |
| image_decode            |   500 |   3.858 |        0.007717 |
| perceptual_hash         |   500 |   2.118 |        0.004235 |
| db_commit               |   500 |   1.421 |        0.002841 |
| db_record_create        |   500 |   0.185 |        0.000370 |
| file_copy               |   500 |   0.120 |        0.000240 |
| content_hash            |   500 |   0.094 |        0.000187 |
| image_open              |   500 |   0.060 |        0.000120 |
| file_stat               |   500 |   0.031 |        0.000061 |
| metadata_extraction     |   500 |   0.003 |        0.000006 |
| processing_invalidation |     1 |   0.021 |               - |
| import_endpoint_commit  |     1 |   0.022 |               - |

Current large-image import conclusion: the top two actionable backend stages are `quality_scoring` and `preview_generation`. File copy, content hashing, database record creation, and database commits are not meaningful bottlenecks in this generated-image run.

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

Recommended next performance step: optimize exactly one confirmed dominant backend import stage, now `quality_scoring`, or validate a 1,000-photo opt-in browser run using the faster preview path before attempting 2,000-photo real browser-backend validation.
