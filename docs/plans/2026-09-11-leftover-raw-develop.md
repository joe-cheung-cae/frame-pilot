# Leftover: RAW fallback develop (no embedded preview) (2026-09-11)

> Language: **English** | [中文](2026-09-11-leftover-raw-develop.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202). S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) shipped `extract_thumb` only. Do not reopen #162 as unfinished. This leftover is fallback LibRaw `postprocess` when no embedded preview exists. FramePilot is not a RAW editor. Do not invent Phase 10 / S10 / 2.3.

**Branch:** `feature/leftover-raw-develop` from `origin/main`. Do not checkout `main` for commits. Do not merge to `main`. Do not squash. Do not force-push. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; [docs/desktop_development_plan.md](../desktop_development_plan.md) §5.6 / §10; [docs/v2_known_limitations.md](../v2_known_limitations.md) Deferred Formats; [docs/api.md](../api.md) RAW paragraph; `apps/api/app/image/raw_preview.py`; `apps/api/app/services/importing.py`.

需求拆解 was documentation contract only. 评审 corrected spec holes against the live RAW import path. This 归档 commit records the 开发 handoff only. Do not implement production Python. Do not tick 开发 or 上线. Do not claim color-managed RAW. Do not invent Phase 10 / S10 / 2.3.

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
5. **Add `open_raw_import_image` (or equivalent).** Try `extract_thumb` first. Call `postprocess` only when thumb fails. Prefer one `rawpy.imread` handle. Reuse `RawPreviewError` for both-path failure so `importing.py` `except RawPreviewError` still works. Keep `RAW_NO_PREVIEW_REASON` **only** on `extract_raw_preview_image`.
6. **Locked `postprocess` kwargs (评审 did not tighten):** `use_camera_wb=True`, `no_auto_bright=True`, `output_bps=8`, `half_size=True`. Confirmed on `tiny_dng_without_preview_bytes()` with rawpy 0.27.1: RGB `uint8` 16×12 (`half_size` of 32×24 CFA). Must not add editor controls. Convert with `Image.fromarray` of a copied array **inside** the `with rawpy.imread` block (numpy buffer is invalid after close).
7. **Never `postprocess` inside `expand_import_paths`.** Folder walk is sync HTTP. RAW extensions collect by suffix only — no `extract_thumb` probe either. HTTP multipart and from-paths call `register_import_file`, **not** `import_image_file` (`import_image_file` is a helper used by one chunked-reader test). `_open_imported_image` must call `open_raw_import_image` so `process_registered_import_photo`, `ensure_photo_derivatives`, and `import_image_file` can develop no-preview files.
8. **Skip reason when thumb and `postprocess` both fail:** `RAW file could not be developed; no embedded preview and demosaic failed`. First skip-without-copy gate is `register_import_file` (and `import_image_file` if used): copy, open, `_cleanup_paths(source_path)` on `RawPreviewError` **before** inserting a Photo row. Live `process_registered_import_photo` only unlinks thumbnail/preview; `_mark_import_photo_failed` leaves originals + a failed Photo. Do **not** make the derivative job the first both-path-fail gate unless 开发 also unlinks originals and leaves no Photo/bytes. `unsupported_image_reason` must not carry this string (its RAW branch is dead: RAW is already in `SUPPORTED_EXTENSIONS`).
9. **Tests:** `tiny_dng_without_preview_bytes()` already builds CFA without JPEG preview. Use it as the **positive** fallback fixture. Garbage bytes still fail both paths. Do not commit camera RAW. Fallback RGB has no JPEG EXIF (`_extract_metadata` stays empty); do not require `capture_time` / `camera_model` and do not add a DNG tag reader.
10. **One draft PR.** Title: `feat: leftover RAW fallback demosaic (no embedded preview)`. Body must say `Refs #202`. Must not say Fixes or Close. Implementer does not merge. Existing draft: [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203).
11. **No `APP_VERSION` bump.** Product string stays `2.1.0-desktop`. No packaged NSIS/DMG, no `desktop.yml` dispatch, no tray / D3.06 / #41.
12. **PyInstaller:** `packaging/pyinstaller/framepilot-api.spec` already lists `rawpy`, `_rawpy`, `numpy`, and `collect_submodules("rawpy")`. `packaging/pyinstaller/hooks/hook-rawpy.py` already `collect_all` + `collect_dynamic_libs`. 评审 confirms **no extra hiddenimports**. Do not add models.

---

## 3. Status board

Leftover RAW fallback develop (no embedded preview)

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202)
- [x] 评审 — adversarial review against live RAW import path
- [x] 归档 — 开发 handoff recorded (this commit); 开发 stays `[ ]`
- [x] 开发 — tests first; `open_raw_import_image` thumb-then-postprocess; invert skip tests; tick leftover-plan 开发 `[x]` in that same commit (do **not** tick 上线)
- [x] 测试 — named pytest + `lint:api`; no camera files
- [x] 上线 — living docs + issue comment; do **not** merge; do **not** invent Phase 10

This 上线 commit ticks **测试** `[x]` (named pytest already green) and **上线** `[x]`. Do not merge to `main`. Do not invent Phase 10. Do not claim color-managed RAW.

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
| `apps/api/app/image/raw_preview.py` | Keep `extract_raw_preview_image` thumb-only. Add `open_raw_import_image` (thumb, then locked `postprocess`). New skip-reason constant on `RawPreviewError` for both-path failure. Copy RGB inside the rawpy context. |
| `apps/api/app/services/importing.py` | `expand_import_paths`: collect RAW by suffix; **no** `extract_thumb` / `postprocess` probe. `register_import_file` remains the skip-without-copy gate (`open_raw_import_image` after copy; unlink `originals/` before Photo). `_open_imported_image` → `open_raw_import_image` (covers `process_registered_import_photo`, `ensure_photo_derivatives`, `import_image_file`). Do not change `unsupported_image_reason` to the new string. |
| `apps/api/tests/raw_helpers.py` | Reuse `tiny_dng_without_preview_bytes()`. Do not add camera files. |
| `apps/api/tests/test_raw_preview.py` | Keep thumb-only assertion on `extract_raw_preview_image`. Add `open_raw_import_image` tests: CFA-without-preview returns RGB; preview files still never `postprocess`; garbage raises the both-path-fail reason. |
| `apps/api/tests/test_import_path_expansion.py` | Invert expand: suffix collect; no skip for missing thumb at expand time. |
| `apps/api/tests/test_import_from_paths.py` | Path import develops CFA-without-preview; garbage still skipped with new reason; no leftover `originals/` bytes. Invert `test_import_from_paths_accepts_avif_and_still_skips_raw` garbage `.dng` reason. |
| `apps/api/tests/test_import_process_export_api.py` | Multipart import same inversion. Preview-present DNG still uses thumb RGB. Invert HEIC/AVIF “still skips raw” garbage `.dng` reason. |
| [docs/api.md](../api.md) (+ zh) | RAW paragraph: fallback demosaic when no embedded preview; still not a RAW editor. |
| [docs/v2_known_limitations.md](../v2_known_limitations.md) (+ zh) | Deferred Formats: this leftover vs color-managed / extra extensions still unscheduled. |
| `develop_plan.md` §1.1 (+ zh) | **Next** names leftover #202. |
| [docs/desktop_development_plan.md](../desktop_development_plan.md) §5.6 / §10 (+ zh) | Split fallback demosaic leftover `[ ]` vs color-managed still deferred. |
| `implement_goals.md` (+ zh) | Living pointer at §1.1 leftover. Do not invent Phase 10. |
| `packaging/pyinstaller/framepilot-api.spec` + `hooks/hook-rawpy.py` | 评审: already collects `rawpy` / `_rawpy` / dynamic libs. **No extra hiddenimports.** Do not add models. |

Live tree today (`origin/main` `110eca7`, reviewed on `feature/leftover-raw-develop`):

- `expand_import_paths` calls `extract_raw_preview_image` and skips on `RawPreviewError` (sync HTTP folder walk).
- HTTP multipart and from-paths call `register_import_file` (copy then probe `extract_raw_preview_image`; cleanup `source_path` on fail **before** Photo).
- `import_image_file` is not the HTTP route; one test uses it. It opens via `_open_imported_image` and cleans `source_path` on `RawPreviewError`.
- `_open_imported_image` / `ensure_photo_derivatives` / `process_registered_import_photo` call `extract_raw_preview_image` only. Derivative-job fail path does **not** unlink originals.
- `RAW_EXTENSIONS = {".arw", ".cr3", ".dng", ".nef"}`. `unsupported_image_reason` RAW branch returns `RAW_NO_PREVIEW_REASON` but is dead (RAW is in `SUPPORTED_EXTENSIONS`).
- `APP_VERSION` is `2.1.0-desktop`.

---

## 6. Test inversion table

| Test (today) | Today | After leftover |
| ---- | ---- | ---- |
| `test_extract_raw_preview_does_not_call_postprocess` | Files **with** preview: `extract_thumb` only | Still green. `extract_raw_preview_image` never `postprocess`. Add the same assertion for `open_raw_import_image` on preview files. |
| `test_extract_raw_preview_missing_thumb_raises` | `tiny_dng_without_preview_bytes()` → `RAW file has no embedded preview; FramePilot does not demosaic` | Still true for `extract_raw_preview_image`. `open_raw_import_image` must demosaic that CFA and return RGB (positive fixture; 评审: locked kwargs succeed, 16×12 `uint8`). Do not require size == `TINY_DNG_PREVIEW_SIZE` as a product rule — it is CFA/2 under `half_size=True`. |
| `test_extract_raw_preview_garbage_bytes_raise` | Garbage `.dng` fails thumb (`LibRawIOError` at `imread`) | `extract_raw_preview_image` still no-preview reason. `open_raw_import_image` / import skip uses the both-path-fail reason. Cleanup `originals/`. |
| `test_expand_includes_dng_with_preview_and_skips_without` | Expand skips `empty.dng` / `garbage.dng` | Expand collects all RAW suffixes (`frame.dng`, `empty.dng`, `garbage.dng`). No `extract_thumb` / `postprocess` here. Skip happens at register. |
| `test_expand_nested_jpegs_and_skips` / `test_expand_includes_avif_and_still_skips_raw` | Garbage `.dng` skipped at expand with no-preview reason | Collect `.dng` by suffix at expand. |
| `test_import_dng_without_preview_is_skipped_without_copy` | Skip + no `originals/` copy | **Invert:** CFA-without-preview imports via fallback; originals copied; no leftover skip. Do not assert EXIF capture_time/camera_model on this path. |
| `test_import_from_paths_accepts_dng_and_skips_no_preview` | `empty.dng` skipped | `empty.dng` (CFA, no JPEG preview) imports. Source fingerprint unchanged. |
| `test_import_accepts_dng_embedded_preview_and_skips_garbage_raw` | Preview DNG imports; garbage skipped with no-preview reason | Preview DNG still thumb-only RGB. Garbage skip uses the both-path-fail reason; no `originals/` bytes. |
| `test_import_accepts_heic_and_still_skips_raw` / `test_import_accepts_avif_and_still_skips_raw` / `test_import_from_paths_accepts_avif_and_still_skips_raw` | Garbage `.dng` skipped with `RAW_NO_PREVIEW_REASON` | Same skip-without-copy; reason becomes the both-path-fail string. |
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

---

## 8. Review findings (评审, 2026-09-11)

Reviewed against the live tree on `feature/leftover-raw-develop` (`65af8e0` on top of `origin/main` `110eca7`). Confirmed:

1. **Leftover, not Phase 10.** `develop_plan.md` §1.1 **Next** names leftover [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202). Desktop §5.6 / §10 split fallback `[ ]` vs color-managed unscheduled. Do not invent Phase 10 / S10 / 2.3. Do not reopen S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162).
2. **`extract_raw_preview_image` stays thumb-only.** Live function never calls `postprocess`. Keep `test_extract_raw_preview_does_not_call_postprocess` green for files **with** a preview.
3. **`expand_import_paths` will not `postprocess`.** Today it probes `extract_raw_preview_image` on the sync HTTP walk. After leftover it collects RAW by suffix only (no thumb probe either).
4. **Skip reason changes only when both paths fail.** `RAW_NO_PREVIEW_REASON` remains the thumb-only helper message. Import skip string is `RAW file could not be developed; no embedded preview and demosaic failed`.
5. **Positive fixture:** `tiny_dng_without_preview_bytes()` is CFA without JPEG preview. 评审 ran locked kwargs: `extract_thumb` → `LibRawNoThumbnailError`; `postprocess` → RGB. Garbage `b"not-a-real-raw"` → `LibRawIOError` on open (both paths fail). Do not commit camera RAW.
6. **Issue number matches GitHub:** [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202). Draft PR [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203) already `Refs #202` (no Fixes/Close).
7. **§1.1 Next names this leftover.** `implement_goals.md` living pointer does too.
8. **PyInstaller already collects `rawpy`.** Spec hiddenimports + `hook-rawpy.py` `collect_all` / `collect_dynamic_libs`. **No extra hiddenimports.**

Holes fixed in this commit (live tree made the 需求拆解 spec incomplete):

1. HTTP uses `register_import_file`, not `import_image_file`. Derivative-job fail does not unlink `originals/`. Register stays the skip-without-copy gate.
2. Test inversion missed `test_import_accepts_heic_and_still_skips_raw`, `test_import_accepts_avif_and_still_skips_raw`, `test_import_from_paths_accepts_avif_and_still_skips_raw`.
3. Reuse `RawPreviewError`; copy RGB inside the rawpy context; fallback RGB has no JPEG EXIF.
4. `unsupported_image_reason` must not become the new skip reason.
5. Double demosaic (register probe + later `_open_imported_image`) is accepted with `half_size=True`. Do not add a cache or editor UI.

Non-holes: kwargs not tightened; extra extensions still out; no `APP_VERSION` bump; 开发 / 上线 stay `[ ]`.

---

## 9. Archive handoff (归档, 2026-09-11)

Reviewed plan is locked for 开发. Status: 需求拆解 `[x]`, 评审 `[x]`, 归档 `[x]`. 开发 is still `[ ]` (no `feat: demosaic RAW without embedded preview` commit on this branch).

**开发 MUST**, in one commit with subject `feat: demosaic RAW without embedded preview`:

1. **Tests first.** Invert skip tests per §6. Use `tiny_dng_without_preview_bytes()` as the positive CFA-without-preview fixture. Garbage bytes still fail both paths. Keep `test_extract_raw_preview_does_not_call_postprocess` green for files **with** a preview. Do not commit camera RAW.
2. Add `open_raw_import_image` that tries `extract_thumb` first, then locked `postprocess` only when thumb fails (`use_camera_wb=True`, `no_auto_bright=True`, `output_bps=8`, `half_size=True`). `extract_raw_preview_image` stays thumb-only and must never call `postprocess`. Copy RGB inside the `with rawpy.imread` block.
3. Invert import: `expand_import_paths` collects RAW by suffix (no `extract_thumb` / `postprocess` probe). `register_import_file` remains the skip-without-copy gate. `_open_imported_image` calls `open_raw_import_image`. Both-path skip reason: `RAW file could not be developed; no embedded preview and demosaic failed`. Cleanup `originals/` copy; no leftover bytes.
4. Tick leftover-plan 开发 `[x]` (en+zh) in **that same commit**.
5. `git push -u origin HEAD`. Do not open a second PR (draft PR is [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203)).
6. **Must not** tick 上线. **Must not** claim color-managed RAW, extra extensions (`.cr2` `.raf` `.orf` `.rw2`), or a RAW editor. Do not bump `APP_VERSION`. Do not invent Phase 10 / S10 / 2.3. Do not reopen S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162).

Do not implement production Python in this 归档 commit. Follow **this reviewed plan** (§2, §5, §6).

Pointers: leftover [#202](https://github.com/joe-cheung-cae/frame-pilot/issues/202); draft PR [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203); S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) stays shipped `extract_thumb` only.

---

## 10. 上线 (上线, 2026-09-11T03:25:56Z)

Named pytest + `lint:api` already green on 测试. This commit records leftover RAW fallback develop in living docs. Status: 需求拆解 `[x]`, 评审 `[x]`, 归档 `[x]`, 开发 `[x]`, 测试 `[x]`, 上线 `[x]`.

Shipped on `feature/leftover-raw-develop` (not merged to `main`): `open_raw_import_image` tries `extract_thumb` first, then locked `postprocess` only when thumb fails. `extract_raw_preview_image` stays thumb-only. Skip when both fail: `RAW file could not be developed; no embedded preview and demosaic failed`. Cleanup `originals/` copy.

Draft PR [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203) `Refs #202`. Do **not** merge. Do **not** invent Phase 10 / S10 / 2.3. Do not reopen S9.04 [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162). Color-managed RAW / extra extensions stay unscheduled. No `APP_VERSION` bump.
