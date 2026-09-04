# Desktop Phase 2 workflow checklist

> Language: **English** | [中文](workflow.zh.md)

Manual GUI pass for D2.08. Automated coverage is `apps/api/tests/test_path_import_process_export_workflow.py` (`from-paths` → process → Pick → CSV/ZIP/folder export; source `st_size` / mtime / hash unchanged).

Do **not** modify or delete original camera files. Copy-mode only. HEIC/RAW/XMP are out of Phase 2.

Live native picker, drag-drop, and OS reveal clicks may stay dated `[~]` on a host without a WebView. HTTP/API coverage must still be `[x]`.

## Setup

- [ ] User-space `rustc` / `cargo` available (`apps/desktop/README.md`). `npm run verify` must not invoke them.
- [ ] From the repo root: `npm run dev:desktop`. Window title is `FramePilot`. Sidecar is loopback with `FRAMEPILOT_DESKTOP=1`.
- [ ] Prepare a throwaway folder of JPEG/PNG/WebP files **outside** the project data directory. Record size and modification time of at least two files.

## Create project

- [ ] Open Create Project (`/projects/new`).
- [ ] Enter a project name. On desktop, **Browse** opens the native directory picker, registers the folder (`POST /api/desktop/project-roots`), then fills **Project data folder**.
- [ ] If the chosen folder already contains files, confirm exactly: `This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?`
- [ ] **Create and Import** lands on Import Images.
- [ ] Dashboard **Open project folder** reveals `root_path` in the OS file manager.

## Import (path import, not WebView File API)

- [ ] **Choose a folder** (or **Choose image files**) uses the native dialog and imports via `POST /api/projects/{id}/imports/from-paths`.
- [ ] Optional: drop files or folders on the import page only. Overlay copy is `Drop files or folders to import`. Dropping elsewhere must not start import.
- [ ] Import job reaches `complete` (or `complete_with_errors` only for skipped unsupported files). **Process Project** stays blocked while import is running.
- [ ] Project copies exist under `{root_path}/originals`. Source folder listing, file sizes, and modification times are unchanged.

## Process

- [ ] **Process Project** → **Run Grouping and Ranking**.
- [ ] Job reaches `complete`. **Open Culling Workspace** is enabled.

## Cull with keyboard

- [ ] Arrows move photo / group.
- [ ] `P` Pick, `M` Maybe, `X` Reject, `U` Unreviewed.
- [ ] `1`–`5` set stars; `0` clears stars.
- [ ] `E` opens export. `Space` / `Z` / `C` / `G` / `F` still work. Modifier chords must not steal those bare keys.

## Export and reveal

- [ ] On Export Selection, keep **Pick** checked. Export **CSV**, then **ZIP**, then **Folder**.
- [ ] Each run shows a local `output_path` under `{root_path}/exports/{csv|zip|folders}`.
- [ ] **Open export folder** reveals that `output_path` (or the project exports root). **Copy Path** still works.
- [ ] Browser/WebView download anchors are not required on desktop (D2.09). Confirm artifacts on disk instead of downloading blobs through the WebView.

## Originals

- [ ] Source files used for import still exist at the same paths.
- [ ] Size and modification time match the values recorded before import.
- [ ] Bytes match (no rewrite, no sidecar next to the originals, no hard-link into `originals` on POSIX).
- [ ] Export folder/ZIP contents are copies from project originals, not the camera card files.

## Record

Date, OS, `APP_VERSION` (`2.0.0-rc2`), and whether native picker / drag / reveal were live `[x]` or dated `[~]`. Do not start Phase 3 from this checklist.
