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
|          2000 |          1000 |              377 |               89 |               54 |         248 |               941 |              915 |               40.15 |

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
