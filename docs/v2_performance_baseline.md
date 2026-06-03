# FramePilot v2 Performance Baseline

This document records local synthetic smoke results for v2.5 reliability validation. These numbers are not a formal benchmark; they provide a reproducible baseline for checking that large local workflows complete without crashes, failed items, or obvious memory growth.

Command:

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
```

Latest local run: 2026-06-03.

| Count | Status | Imported | Processed | Failed Items | Groups | Import Seconds | Process Seconds | Export Seconds | Peak RSS MB |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | complete | 100 | 100 | 0 | 55 | 0.448 | 0.320 | 0.075 | 127.86 |
| 500 | complete | 500 | 500 | 0 | 264 | 1.778 | 1.733 | 0.286 | 147.33 |
| 2000 | complete | 2000 | 2000 | 0 | 1037 | 8.034 | 14.602 | 1.150 | 219.33 |

The smoke uses generated local JPEG images and default CSV, ZIP, and folder exports. Each run writes temporary sources, project data, and export artifacts under the selected output directory.

Use the command above for current-machine validation before relying on these timings. Hardware, Python version, filesystem speed, and image dimensions will change the absolute values.
