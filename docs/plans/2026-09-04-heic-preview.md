# Phase 8 Implementation Plan — HEIC Preview (2026-09-04)

> Language: **English** | [中文](2026-09-04-heic-preview.zh.md)

**Umbrella:** [#150](https://github.com/joe-cheung-cae/frame-pilot/issues/150)  
**This gate:** [#151](https://github.com/joe-cheung-cae/frame-pilot/issues/151) — implement H8.01–H8.06 (RAW, AVIF, XMP, and signing are not DoD)  
**Related:** `develop_plan.md` §1.1, §7, §10.5, §16.7; `apps/api/app/services/importing.py` (`SUPPORTED_EXTENSIONS`, `PLANNED_HEIC_EXTENSIONS`); `docs/v2_known_limitations.md` Deferred Formats

For Goal Mode: implement **one task id at a time**. Do not start the next task until the current task is implemented, tested, reviewed, and committed.

---

## 1. Why this slice

JPEG/PNG/WebP culling, desktop RC, durable jobs, and processing cancel are on `main`. Packaged Windows GUI lifecycle QA ([#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)) is closed as Windows-only.

The next user-visible hole is **iPhone still photos**: import currently skips `.heic` / `.heif` with “HEIC files are not supported yet”. `develop_plan.md` §7 already said HEIC comes after the processing architecture is stable.

This slice decodes HEIC/HEIF **locally** into the existing derivative/scoring pipeline. It is **preview support**, not a RAW developer, not XMP, and not a signed store release.

---

## 2. Locked decisions

1. **Local-first only.** No cloud decode, no login, no payment, no bundled neural models, no large files committed to git.
2. **Decoder:** add `pillow-heif` and call `register_heif_opener()` once at API startup so existing `Image.open` / `ImageOps.exif_transpose` / `.convert("RGB")` paths work. Do **not** parse HEIC as “embedded JPEG only” — typical iPhone HEIC is HEVC, not a JPEG in the box.
3. **Copy the original bytes.** HEIC/HEIF files go under `{root_path}/originals/` unchanged (same copy rules as JPEG). Thumbnails and previews stay **WebP**. Never modify or delete the source file.
4. **Score and group on decoded RGB**, same as JPEG. Do not add a parallel HEIC scoring stack.
5. **Primary image only.** If pillow-heif reports multiple images, use the primary frame. Do not import Live Photo `.mov` companions. `.mov` stays unsupported.
6. **HDR / gain maps:** decode whatever primary RGB pillow-heif gives. Do not implement gain-map tone mapping in this slice. Document the limitation.
7. **RAW stays skipped** (`.arw`, `.cr3`, `.dng`, `.nef`) with the existing explicit reason. Do not extract RAW previews here.
8. **AVIF is out of scope.** Even if the plugin can open AVIF, `SUPPORTED_EXTENSIONS` must not add `.avif`.
9. **Export copies the original HEIC**, not a converted JPEG. Add `.heic` / `.heif` to `STORED_IMAGE_EXTENSIONS` so ZIP uses `ZIP_STORED` (already-compressed). CSV/folder/ZIP already copy `project_copy_path` once the file is in `originals/`.
10. **No XMP write** ([#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117) stays `not_planned`).
11. **Tests generate tiny HEIC in-process** via pillow-heif. Do not commit camera HEIC. Garbage `.heic` bytes follow the broken-JPEG path (failed photo after copy), not the old “unsupported extension” skip.
12. **Packaging:** PyInstaller must collect `pillow_heif` and its bundled libheif binaries. Unsigned NSIS/DMG only. Do not sign. Do not bump `APP_VERSION`.
13. **License note:** `pillow-heif` is BSD-3-Clause; wheels ship **LGPL** `libheif` (and codecs). Document that in known limitations / this plan. Do not vendor libheif source into the MIT tree.
14. **Bilingual living docs**; English code, comments, tests, commit messages.
15. **Out of scope:** export job cancel, J7.07 pause, D3.06 tray, auto-update, desktop 2.2, 500/1000/2000 real-browser default CI, `:large` GUI RSS.

---

## 3. Status board

Phase 8 — HEIC preview (post #144)

- [x] H8.01 pillow-heif dependency and opener registration
- [ ] H8.02 Import accepts `.heic` / `.heif`
- [ ] H8.03 Process and export original HEIC
- [ ] H8.04 Web import accept + copy
- [ ] H8.05 Frozen sidecar collects pillow-heif
- [ ] H8.06 Docs close-out

---

## 4. File map

| Path | Create / edit | Tasks |
| ---- | ------------- | ----- |
| `apps/api/pyproject.toml` | Add `pillow-heif`; bump Pillow only if the plugin requires it | H8.01 |
| `apps/api/app/image/heif_support.py` | New: idempotent `ensure_heif_opener()` | H8.01 |
| `apps/api/app/main.py` | Call `ensure_heif_opener()` in `create_app` | H8.01 |
| `apps/api/app/services/importing.py` | Register opener; move HEIC extensions into `SUPPORTED_EXTENSIONS` | H8.01–H8.02 |
| `apps/api/app/services/exporting.py` | `STORED_IMAGE_EXTENSIONS` add `.heic`, `.heif` | H8.03 |
| `apps/api/tests/test_import_process_export_api.py` | Invert HEIC skip; add decode/export | H8.02–H8.03 |
| `apps/api/tests/test_import_from_paths.py` | Invert `shot.heic` skip | H8.02 |
| `apps/api/tests/test_import_path_expansion.py` | Invert `shot.heic` skip | H8.02 |
| `apps/api/tests/test_path_import_process_export_workflow.py` | HEIC original through process+export | H8.03 |
| `apps/web/src/components/ImportPanel.tsx` (+ test) | `accept` includes HEIC | H8.04 |
| `packaging/pyinstaller/framepilot-api.spec` (+ hook if needed) | hiddenimports + native libs | H8.05 |
| `scripts/sidecar-smoke.sh` or packaging test | Frozen decode smoke | H8.05 |
| `docs/api.md`, `docs/architecture.md`, `docs/v2_known_limitations.md`, `README.md`, `docs/desktop_user_guide.md` (+ zh) | Formats | H8.06 |
| `CHANGELOG.md` (+ zh) | Unreleased Phase 8 | H8.06 |
| This plan (+ zh) | Tick §3 per completed task | each |

---

## 5. Current code (do not regress)

| Behavior | Where |
| -------- | ----- |
| HEIC/HEIF skipped before copy | `is_supported_image` / `unsupported_image_reason` — “HEIC files are not supported yet…” |
| RAW skipped | same helper — keep |
| `Image.open` without HEIF plugin | `importing.py` derivative/score path |
| Export copies any file in `originals/` | `copy_selected_files` / `zip_selected_files`; `STORED_IMAGE_EXTENSIONS` only picks ZIP compression |
| Web file picker | `ImportPanel.tsx` `accept="image/jpeg,image/png,image/webp"` |
| Frozen sidecar | `packaging/pyinstaller/framepilot-api.spec` lists JPEG/PNG/WebP plugins only |
| Asserted skip tests | `test_import_reports_heic_and_raw_as_planned_unsupported_formats`, path-expansion `shot.heic` |

JPEG/PNG/WebP import, cancel, reclaim, and desktop quit must stay green.

---

## 6. Task specs

### H8.01 — pillow-heif dependency and opener registration

**Depends on:** none

**Contract:**

- Add `pillow-heif` to `apps/api/pyproject.toml` runtime dependencies. Choose a version with CPython 3.11 wheels for manylinux, macOS, and win_amd64. If that version requires Pillow 11, bump `pillow` in the same commit; otherwise keep `pillow>=10.4.0`.
- New `apps/api/app/image/heif_support.py` with `ensure_heif_opener()` that calls `pillow_heif.register_heif_opener()` and is safe to call twice.
- `create_app()` calls it. `importing.py` also calls it at module import (tests that import the service without `create_app` still decode).
- Do **not** change `SUPPORTED_EXTENSIONS` yet. HEIC files remain skipped until H8.02.
- Test helper (test module only): write a tiny RGB image to HEIC bytes via pillow-heif; `Image.open` after `ensure_heif_opener()` succeeds and `.convert("RGB")` has the expected size.
- Do not register an AVIF opener even if the library offers one.

**H8.01 non-goals:** no import-extension change; no UI; no PyInstaller; no docs close-out; no RAW; no `APP_VERSION` bump.

**Commit:** `feat: register pillow-heif opener for HEIC decode`

---

### H8.02 — Import accepts `.heic` / `.heif`

**Depends on:** H8.01

**Contract:**

- Add `.heic` and `.heif` to `SUPPORTED_EXTENSIONS`. Remove them from `PLANNED_HEIC_EXTENSIONS` (or delete that set if empty).
- `unsupported_image_reason` no longer returns the HEIC planned-skip string. RAW string stays.
- Multipart `/import` and `from-paths` copy a valid tiny HEIC into `originals/`, write WebP thumbnail+preview, extract EXIF when present, leave source size/mtime/bytes unchanged.
- Garbage `.heic` (`b"not-a-real-heic"`) is **not** “unsupported format”. It is a failed import item (same family as `broken.jpg`): do not crash the job.
- Invert:
  - `test_import_reports_heic_and_raw_as_planned_unsupported_formats` — HEIC imports; RAW still skipped; no `originals/camera.heic` was the old assertion, now the copy **must** exist for a valid fixture HEIC.
  - `test_import_from_paths.py` / `test_import_path_expansion.py` `shot.heic` cases.

**H8.02 non-goals:** no process/export workflow test (H8.03); no web `accept` (H8.04); no PyInstaller (H8.05); no living-docs sweep (H8.06).

**Commit:** `feat: import HEIC and HEIF stills`

---

### H8.03 — Process and export original HEIC

**Depends on:** H8.02

**Contract:**

- Path-import a tiny HEIC, `POST /process`, then CSV + ZIP + folder export of the selected photo.
- Grouping/ranking may be a single-photo group; that is enough.
- ZIP/folder payload is the **original HEIC bytes**, not a JPEG conversion. `STORED_IMAGE_EXTENSIONS` includes `.heic` and `.heif`.
- Source HEIC size/mtime/bytes unchanged after import, process, and export.
- Existing JPEG process/export tests stay green.

**H8.03 non-goals:** no UI accept; no PyInstaller; no docs sweep; no export-job cancel.

**Commit:** `feat: process and export original HEIC`

---

### H8.04 — Web import accept + copy

**Depends on:** H8.02 (can land after H8.03)

**Contract:**

- `ImportPanel.tsx` file inputs `accept` include HEIC (`image/heic`, `image/heif`, `.heic`, `.heif`) in addition to JPEG/PNG/WebP.
- Any user-visible “JPEG, PNG, and WebP only” copy in the import panel or empty-state strings that would contradict HEIC support is updated. RAW remains called out as unsupported.
- `ImportPanel.test.tsx` covers the accept string (or equivalent).
- Do not change desktop native folder picker code unless it hard-filters extensions in TS (path-import uses the API list).

**H8.04 non-goals:** no API behavior change; no PyInstaller; no docs sweep beyond UI strings.

**Commit:** `feat: accept HEIC in the import panel`

---

### H8.05 — Frozen sidecar collects pillow-heif

**Depends on:** H8.01 (can start after H8.02 if import tests already prove decode)

**Contract:**

- `framepilot-api.spec` (and a hook if PyInstaller does not auto-collect) includes `pillow_heif` hiddenimports and bundled native libs (`libheif` and codec DLLs/so/dylib from the wheel).
- Keep existing JPEG/PNG/WebP Pillow plugins. Do not strip scipy.
- Frozen sidecar smoke still unsets `PYTHONPATH`. Add a decode check: frozen environment can `ensure_heif_opener()` + `Image.open` a generated tiny HEIC, **or** an equivalent import through the frozen binary. `/health` stays the minimum gate.
- Installer size: pillow-heif wheels are small next to scipy/numpy. Stay under the documented **400 MB unpacked** D4.06 threshold; do not treat the extra native libs as a cue to drop codecs.
- Do not sign. Do not run packaged NSIS/DMG GUI as this task’s DoD.

**H8.05 non-goals:** no docs sweep; no `APP_VERSION`; no desktop.yml signing secrets.

**Commit:** `packaging: collect pillow-heif in the frozen sidecar`

---

### H8.06 — Docs close-out

**Depends on:** H8.02–H8.05 landed (or land last on the same branch)

**Contract:** bilingual pages match live behavior. Do not claim RAW, AVIF, HDR tone-mapping, XMP, or signed builds.

Files:

- `README.md` + `README.zh.md`
- `docs/api.md` + `docs/api.zh.md`
- `docs/architecture.md` + `docs/architecture.zh.md`
- `docs/v2_known_limitations.md` + `docs/v2_known_limitations.zh.md`
- `docs/desktop_user_guide.md` + `docs/desktop_user_guide.zh.md` (formats / import)
- `CHANGELOG.md` + `CHANGELOG.zh.md` — Unreleased `### Phase 8 — HEIC preview`
- This plan + zh — tick §3 and §7 in the **implementation** commit only

Per-file:

- **README / known limitations:** HEIC/HEIF stills import locally; RAW still skipped; originals unchanged; derivatives are WebP; no XMP.
- **api / architecture:** import list includes HEIC/HEIF; decode via pillow-heif; export original bytes.
- **CHANGELOG:** local HEIC preview; RAW still deferred; no version bump, signing, or XMP.

Do **not** edit `develop_plan.md` in the implementation commit if this docs-pointer PR already named Phase 8 as next (avoid a second pointer fight). After Phase 8 merges, a later pointer PR can mark it shipped.

**H8.06 non-goals:** no production code; do not close the umbrella via `Fixes` from a docs-only commit if implement tasks are still open.

**Commit:** `docs: close out Phase 8 HEIC preview`

---

## 7. Phase 8 Definition of Done

- [ ] Valid `.heic` / `.heif` stills import, copy to `originals/`, and get WebP thumb/preview
- [ ] Source HEIC bytes/mtime unchanged through import, process, and export
- [ ] Scoring/grouping/ranking run on decoded RGB without a second pipeline
- [ ] ZIP/folder export ships the original HEIC; CSV lists it
- [ ] Garbage HEIC fails that file, does not crash the job
- [ ] RAW extensions still skipped with the existing reason
- [ ] Web import accept includes HEIC
- [ ] Frozen sidecar can decode HEIC (plugin + native libs collected)
- [ ] Bilingual docs match; CHANGELOG Unreleased has Phase 8
- [ ] `npm run test:api`, `npm run test:web`, and `npm run verify` green
- [ ] No `APP_VERSION` bump, no signing, no XMP, no RAW preview, no AVIF, no J7.07

---

## 8. Verification commands

```bash
npm run test:api
npm run lint:api
npm run test:web
npm run typecheck
npm run verify
```

Targeted while iterating:

```bash
.venv/bin/pytest apps/api/tests/test_import_process_export_api.py apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_path_expansion.py -q -k 'heic or HEIC or heif'
npm run test:web
```

Do not sign. Do not treat unsigned as signed. Do not reopen #117 or D3.06.

---

## 9. Explicit non-goals

- RAW embedded preview (DNG/ARW/CR3/NEF)
- AVIF
- XMP sidecar write
- HDR gain-map display
- Live Photo video
- Export job cancel / export reclaim
- J7.07 pause/resume
- Signing / store release / `APP_VERSION` bump
- D3.06 tray, auto-update, desktop 2.2
- Committing camera HEIC or libheif source

---

## 10. Workflow execution

Each H8.01–H8.06 task is a **separate** workflow (workflows cannot launch other workflows). Do not implement RAW or XMP in those workflows.
