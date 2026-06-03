# FramePilot

FramePilot is a local-first AI-assisted photo culling web app. The MVP keeps originals on the user's machine, generates local previews, computes explainable technical scores, groups similar frames, recommends the strongest image in each group, and lets the user override every decision.

## Current MVP

- Next.js, React, TypeScript, Tailwind CSS frontend.
- FastAPI, Pydantic, SQLModel, SQLite backend.
- Local project folders with originals, thumbnails, previews, exports, and cache directories.
- JPEG, PNG, and WebP imports.
- Deterministic thumbnail and preview generation.
- Basic metadata extraction and explainable image quality scoring.
- Lightweight local face and eye-open heuristic scoring.
- Lightweight embedding approximation for near-duplicate grouping.
- Group-focused culling with recommendation-first review ordering.
- Pick, Maybe, Reject, and Unreviewed statuses.
- Keyboard review shortcuts: arrows, P, M, X, U, 1-5, Space, and G.
- CSV, folder, and ZIP export modes with unique local export outputs.

## Setup

```bash
npm run install:all
```

## Run Locally

```bash
npm run dev
```

The web app runs at `http://localhost:3000`. The local API runs at `http://127.0.0.1:8000`.

Backend data is written to `.framepilot-data` by default. Set `FRAMEPILOT_DATA_DIR` to use another local project data location.

Typical workflow:

1. Create a project.
2. Import JPEG, PNG, or WebP files. Valid files are imported even if some selected files are skipped.
3. Run processing to rebuild groups and recommendations.
4. Review photos by group and mark Pick, Maybe, Reject, or Unreviewed.
5. Export one or more selected statuses to CSV, folder, or ZIP.

## Verify

```bash
npm run test
```

This runs backend unit/API tests and a frontend production build.

Run browser E2E coverage separately:

```bash
npm run test:e2e
```

## Privacy

The MVP does not upload originals or generated previews to any remote service. Imported images are copied into the local project directory so originals are never modified.

Face and eye-open scores are computed locally with a deterministic color and luminance heuristic. They are MVP ranking hints, not a bundled professional face detection or biometric model.
