# Leftover: RAW fallback develop (no embedded preview) (2026-09-11)

> Language: **English** | [中文](2026-09-11-leftover-raw-develop.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202). S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) shipped `extract_thumb` only. Do not reopen #162 as unfinished. This leftover is fallback LibRaw `postprocess` when no embedded preview exists. FramePilot is not a RAW editor. Do not invent Phase 10 / S10 / 2.3.

**Branch:** `feature/leftover-raw-develop` from `origin/main`. Do not checkout `main` for commits. Do not merge to `main`. Do not squash. Do not force-push. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; [docs/desktop_development_plan.md](../desktop_development_plan.md) §5.6 / §10; [docs/v2_known_limitations.md](../v2_known_limitations.md) Deferred Formats; [docs/api.md](../api.md) RAW paragraph; `apps/api/app/image/raw_preview.py`; `apps/api/app/services/importing.py`.

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch is closed. S9.04 copied original RAW bytes and extracted an embedded JPEG/bitmap preview. Files without a thumb are skipped with `RAW file has no embedded preview; FramePilot does not demosaic` and are not copied into `originals/`.

Some real DNG/ARW/CR3/NEF files have no usable embedded preview. Culling still needs an RGB still. That is a leftover of S9.04, not a new product phase.

This leftover adds a **fallback demosaic** only when `extract_thumb` fails. It does not make FramePilot a RAW editor, a color-managed developer, or Phase 10.

Do **not** invent Phase 10 / S10 / 2.3. Product string stays `2.1.0-desktop`. Do not bump `APP_VERSION`. Do not sign. Do not claim SmartScreen-clean or store listing.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **Not a RAW editor.** No exposure / white-balance UI. No color-managed pipeline. No extra extensions (`.cr2`, `.raf`, `.orf`, `.rw2`). Keep `.dng`, `.arw`, `.cr3`, `.nef` only.
3. **Originals unchanged.** Never modify or delete camera files. Copy into `{project}/originals/` only. Write WebP derivatives separately.
4. **`extract_raw_preview_image` stays thumb-only.** It must never call `postprocess`. Keep `test_extract_raw_preview_does_not_call_postprocess` green for files **with** a preview.
5. **Add `open_raw_import_image` (or equivalent).** Try `extract_thumb` first. Call `postprocess` only when thumb fails.
6. **Locked `postprocess` kwargs:** `use_camera_wb=True`, `no_auto_bright=True`, `output_bps=8`, `half_size=True`. Review may tighten; must not add editor controls.
7. **Never `postprocess` inside `expand_import_paths`.** That path is sync HTTP. RAW extensions collect by suffix. Develop or skip only in `register_import_file` / `import_image_file` / import derivative job (`_open_imported_image` / `ensure_photo_derivatives`).
8. **Skip reason when thumb and `postprocess` both fail:** `RAW file could not be developed; no embedded preview and demosaic failed`. Cleanup any `originals/` copy. No leftover bytes.
9. **Tests:** `tiny_dng_without_preview_bytes()` already builds CFA without JPEG preview. Use it. Garbage bytes still fail both paths. Do not commit camera RAW.
10. **One draft PR.** Title: `feat: leftover RAW fallback demosaic (no embedded preview)`. Body must say `Refs #202`. Must not say Fixes or Close. Implementer does not merge.
11. **No `APP_VERSION` bump.** No packaged NSIS/DMG, no `desktop.yml` dispatch, no tray / D3.06 / #41.

---

## 3. Status board

Leftover RAW fallback develop (no embedded preview)

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)
- [ ] 评审 — adversarial review against live RAW import path
- [ ] 归档 — leftover board ready for 开发
- [ ] 开发 — `open_raw_import_image` fallback `postprocess` when thumb fails
- [ ] 测试 — named pytest + `lint:api`; no camera files
- [ ] 上线 — living docs + issue comment; do **not** merge; do **not** invent Phase 10

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 开发; 上线; §2.2; Phase 10 |
| 评审 + 归档 | leftover board 评审 + 归档 | 开发; 上线 |
| 开发 + named pytest green | leftover board 开发 + 测试 | 上线; color-managed RAW; extra extensions; store listing |
| 上线 docs on this branch | leftover board 上线; §1.1 leftover named | merge to `main`; §2.2 re-tick; Phase 10; SmartScreen-clean |

---

## 5. File map

| File | Role |
| ---- | ---- |
| `apps/api/app/image/raw_preview.py` | Keep `extract_raw_preview_image` thumb-only. Add `open_raw_import_image` (thumb, then locked `postprocess`). New skip-reason constant for both-path failure. |
| `apps/api/app/services/importing.py` | `expand_import_paths`: collect RAW by suffix; **no** `extract_thumb` / `postprocess` probe. `register_import_file`, `import_image_file`, `_open_imported_image`, `ensure_photo_derivatives`: develop or skip via `open_raw_import_image`. Cleanup `originals/` on both-path failure. |
| `apps/api/tests/raw_helpers.py` | Reuse `tiny_dng_without_preview_bytes()`. Do not add camera files. |
| `apps/api/tests/test_raw_preview.py` | Keep thumb-only assertion. Add fallback-develop tests for CFA-without-preview vs garbage. |
| `apps/api/tests/test_import_path_expansion.py` | Invert expand: suffix collect; no skip for missing thumb at expand time. |
| `apps/api/tests/test_import_from_paths.py` | Path import develops CFA-without-preview; garbage still skipped with new reason; no leftover `originals/` bytes. |
| `apps/api/tests/test_import_process_export_api.py` | Multipart import same inversion. Preview-present DNG still uses thumb RGB. |
| [docs/api.md](../api.md) (+ zh) | RAW paragraph: fallback demosaic when no embedded preview; still not a RAW editor. |
| [docs/v2_known_limitations.md](../v2_known_limitations.md) (+ zh) | Deferred Formats: this leftover vs color-managed / extra extensions still unscheduled. |
| `develop_plan.md` §1.1 (+ zh) | **Next** names leftover #202. |
| [docs/desktop_development_plan.md](../desktop_development_plan.md) §5.6 / §10 (+ zh) | Split fallback demosaic leftover `[ ]` vs color-managed still deferred. |
| `implement_goals.md` (+ zh) | Living pointer at §1.1 leftover. Do not invent Phase 10. |
| `packaging/pyinstaller/framepilot-api.spec` | Verify-only: `rawpy` already collected for S9.04. Do not add models. |

Live tree today (`origin/main` `110eca7`):

- `expand_import_paths` calls `extract_raw_preview_image` and skips on `RawPreviewError` (sync HTTP).
- `register_import_file` copies then probes `extract_raw_preview_image`; cleanup on fail.
- `_open_imported_image` / `import_image_file` / `ensure_photo_derivatives` call `extract_raw_preview_image` only.
- `RAW_EXTENSIONS = {".arw", ".cr3", ".dng", ".nef"}`.

---

## 6. Test inversion table

| Test (today) | Today | After leftover |
| ---- | ---- | ---- |
| `test_extract_raw_preview_does_not_call_postprocess` | Files **with** preview: `extract_thumb` only | Still green. `extract_raw_preview_image` never `postprocess`. |
| `test_extract_raw_preview_missing_thumb_raises` | `tiny_dng_without_preview_bytes()` → `RAW file has no embedded preview; FramePilot does not demosaic` | Still true for `extract_raw_preview_image`. `open_raw_import_image` must demosaic that CFA and return RGB. |
| `test_extract_raw_preview_garbage_bytes_raise` | Garbage `.dng` fails thumb | Garbage still fails thumb **and** `postprocess`. Import skip + cleanup. |
| `test_expand_includes_dng_with_preview_and_skips_without` | Expand skips `empty.dng` / `garbage.dng` | Expand collects all RAW suffixes. No `postprocess` here. Skip happens later. |
| `test_expand_nested_jpegs_and_skips` / `test_expand_includes_avif_and_still_skips_raw` | Garbage `.dng` skipped at expand with no-preview reason | Collect `.dng` by suffix at expand. |
| `test_import_dng_without_preview_is_skipped_without_copy` | Skip + no `originals/` copy | Import/develop via fallback. If both paths fail: skip `RAW file could not be developed; no embedded preview and demosaic failed`; cleanup copy; no leftover bytes. |
| `test_import_from_paths_accepts_dng_and_skips_no_preview` | `empty.dng` skipped | `empty.dng` (CFA, no JPEG preview) imports if demosaic works. Source fingerprint unchanged. |
| `test_import_accepts_dng_embedded_preview_and_skips_garbage_raw` | Preview DNG imports; garbage skipped | Preview DNG still thumb-only RGB. Garbage skip uses the both-path-fail reason. |
| Extra extensions | `.cr2` / `.raf` / `.orf` / `.rw2` unsupported | Unchanged. Out of scope. |

Do not commit camera RAW. Named pytest for 测试: `test_raw_preview.py`, `test_import_path_expansion.py`, `test_import_from_paths.py`, RAW cases in `test_import_process_export_api.py`, plus `npm run lint:api`.

---

## 7. Non-goals

- Phase 10 / S10 / 2.3.
- RAW editor: exposure, white balance, tone curve, color-managed develop.
- Extra RAW extensions: `.cr2`, `.raf`, `.orf`, `.rw2`.
- `postprocess` inside `expand_import_paths`.
- Calling `postprocess` from `extract_raw_preview_image`.
- Auto-download/install, processing pool, Redis/Celery.
- SmartScreen / store listing, tray / D3.06, `APP_VERSION` bump.
- Packaged NSIS/DMG, `desktop.yml` dispatch, signing, notarize.
- Camera photos in git, certs, model weights, cloud upload/login/payment.
- Second PR. Merge to `main`. Fixes/Close on the leftover issue from this PR.
