# Phase 5 Full Review (Bugbot + Security)

> Language: **English** | [中文](phase5_full_review.zh.md)

Review date: 2026-08-29.

Combined engineering review of **Phase 5 — Testing, docs, and stabilization** for FramePilot desktop `2.1.0-desktop`, run via Bugbot and Security Review subagents.

## 1. Verdict

Phase 5 is **docs / versioning / release bookkeeping** on top of Phases 0–4. It is suitable to keep as the desktop RC track close-out, with **one medium correctness finding** on D5.03 evidence labeling.

- **Bugbot:** 1 finding (medium).
- **Security:** no medium+ issues in this diff.
- **Security ops notes (below bar):** unsigned installers, localhost `/api/meta`, sidecar log `data_dir` — pre-existing, documented; track for public signed release.

## 2. Scope and method

| Item | Value |
| ---- | ----- |
| Workspace | `/home/joe/repo/frame-pilot` |
| Checked-out tip | `main` @ `a3819dd` (`docs: close out Phase 5 DoD with evidence (#95)`) |
| Diff base | `f4cee3d` (`Merge pull request #77…`) via local ref `review/phase5-base` |
| Diff mode | Branch changes vs `review/phase5-base` |
| Range | Phase 5 only: D5.01–D5.05 (+ inventory / docs design / DoD close-out) |
| Orchestration | Parallel `bugbot` + `security-review` subagents |

### Commits in range

| SHA | Summary |
| ---- | ------- |
| `45b13df` | docs: inventory Phase 5 requirements (#80) |
| `e0b4f82` | docs: design Phase 5 documentation plan (#83) |
| `38d7823` | docs: add desktop test matrix (#85) — **D5.01** |
| `66e42b3` | docs: add desktop install and data-dir instructions (#87) — **D5.02** |
| `3ce7f11` | docs: record desktop performance notes (#89) — **D5.03** |
| `97c03d9` | release: 2.1.0-desktop rc (#91) — **D5.04** |
| `a0b45e2` | docs: document desktop 2.1 known limitations (#93) — **D5.05** |
| `a3819dd` | docs: close out Phase 5 DoD with evidence (#95) |

### Surfaces touched

Documentation (testing matrix, user guide, performance baseline, known limitations, architecture, packaging plan, Phase 5 plans), bilingual counterparts, README pointers, `CHANGELOG`, and version bump across `APP_VERSION` / `pyproject.toml` / package manifests / Tauri / Cargo. No new API routes, middleware, Tauri capabilities, or CI workflows in this range.

## 3. Bugbot findings

| Severity | Location (file:line) | Finding |
| -------- | -------------------- | ------- |
| medium | `docs/v2_performance_baseline.md:33` | D5.03 section titled **Desktop path-import performance** records results from `npm run perf:api`, which calls multipart `POST /api/projects/{id}/import`, not desktop `POST .../imports/from-paths`. Import seconds / peak RSS are API upload-path evidence, not filesystem path-import evidence, yet Phase 5 close-out treats D5.03 as done. |

### Bugbot detail

`apps/api/app/devtools/performance_smoke.py` uploads via `/import` with `files=…`. The baseline text calls this “path-equivalent synthetic import,” which softens but does not fix the mismatch with D5.03’s acceptance intent (“100-photo **path-import** + process RSS”) and the section heading. Packaging plan / feasibility notes repeat the same `perf:api` evidence.

**Suggested follow-up (not done in this review):** either (a) add a from-paths smoke and re-measure, or (b) rename/clarify D5.03 docs and DoD language so they claim API/sidecar RSS via multipart import only, with true path-import marked pending.

## 4. Security findings

| Severity | Location (file:line) | Finding |
| -------- | -------------------- | ------- |
| — | — | No medium, high, or critical issues in this diff. |

### Areas reviewed (clear)

| Area | Result |
| ---- | ------ |
| Path / `data_dir` disclosure via `/api/meta` | Pre-existing; loopback Host; docs only |
| Loopback / CORS / LAN claims in testing matrix | Matches implementation; no widen guidance |
| Unsigned NSIS/DMG messaging | Consistent with signing runbook; accepted RC posture |
| Secrets in docs/CI | None; host label only |
| Unsafe install/test guidance | Aligns with local-first threat model |
| Version / menu / `tauri.conf.json` bumps | No CSP/capability change |

### Below-threshold ops notes

1. **Unsigned artifacts** — MITM/substitution until Authenticode + notarization (`docs/desktop_signing.md`).
2. **`GET /api/meta` on localhost** — unauthenticated install metadata for any same-machine client that can reach the port; unchanged, now more visible in the user guide.
3. **Sidecar ready line / logs** — `data_dir=` on stdout and in `{data_dir}/logs/sidecar.log`; same-user local visibility.

## 5. Phase 5 DoD snapshot (review lens)

| Gate | Review note |
| ---- | ----------- |
| D5.01 Test matrix | Present (`docs/desktop_testing.md` + zh); commands and security rows look coherent |
| D5.02 User docs | User guide + README pointers; copy-not-move / data-dir covered |
| D5.03 Perf notes | Recorded, but **evidence path ≠ path-import** (Bugbot medium) |
| D5.04 Version RC | `2.1.0-desktop` surfaces updated with changelog |
| D5.05 Known limitations | Desktop 2.1 bullets present; unsigned / WSL GUI / tray deferred called out |

## 6. Recommendation

1. Keep Phase 5 close-out on `main` for the internal desktop RC track.
2. Fix or explicitly re-scope D5.03 labeling before treating path-import performance as verified — **[#96](https://github.com/joe-cheung-cae/frame-pilot/issues/96)** (docs clarify) and **[#97](https://github.com/joe-cheung-cae/frame-pilot/issues/97)** (from-paths measurement follow-up).
3. Before any **public signed** release, finish signing/notarization and consider checksum / provenance language in the user guide — **[#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98)**.

---

Generated by parallel Bugbot + Security Review subagents on 2026-08-29. Diff base: `f4cee3d` … tip: `a3819dd`.

### Tracking issues (filed from this review)

| Issue | Type | Title |
| ----- | ---- | ----- |
| [#96](https://github.com/joe-cheung-cae/frame-pilot/issues/96) | Bug | Clarify D5.03 evidence is multipart `perf:api`, not `from-paths` |
| [#97](https://github.com/joe-cheung-cae/frame-pilot/issues/97) | Feature | Measure desktop `from-paths` path-import sidecar RSS |
| [#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98) | Task | Public signed-release hardening from security review |
