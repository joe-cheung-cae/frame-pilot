# Desktop Deep Review (apps/desktop, packaging, sidecar API)

> Language: **English** | [中文](desktop_deep_review.zh.md)

Review date: 2026-09-01.

Docs-only engineering review of FramePilot desktop `2.1.0-desktop` plus desktop-related API (sidecar CLI, path import, job reclaim, data-dir, origin/host) at `main` `011fb61c745cf0eaac103ec3998db46095ace1cf`. Opened from [GitHub issue #118](https://github.com/joe-cheung-cae/frame-pilot/issues/118).

This is **not** product export. **XMP is out of scope** ([#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117) is closed). No production code was changed in this review.

## 1. Verdict

The desktop shell, localhost sidecar, path-import copy path, and Phase 6 reclaim-on-startup default are **suitable to keep as the internal desktop RC**. Safety red lines hold on the shipped path: originals are copied not modified; the sidecar binds `127.0.0.1` only; there is no cloud/updater/telemetry; Tauri does not set a wide project-root allowlist.

There are **no critical or high findings**. Three **medium** items remain for a follow-up PR after this review is rebase-merged: allowlist env is not rejected when an operator sets `$HOME`/`/`/a drive root; `opener:default` is wider than reveal-in-folder; Windows frozen-sidecar smoke can be shadowed by `PYTHONPATH` and the spec omits `uvicorn.loops.asyncio`.

**Do not start those fixes in this PR.**

## 2. Scope and method

| Item | Value |
| ---- | ----- |
| Workspace | `/workspace` |
| Checked-out tip / base | `main` @ `011fb61c745cf0eaac103ec3998db46095ace1cf` (`docs: close D3.04 with dated system theme WebView run`) |
| Diff mode | Tree review of desktop + packaging + desktop-related API/shared web (not a Phase 5-only delta) |
| Product version | `2.1.0-desktop` |
| Compared against | `docs/plans/2026-08-18-desktop-packaging.md`, Phase 6 `docs/plans/2026-08-29-phase6-durable-jobs.md` (incl. §7 default-on), `AGENTS.md` / `develop_plan.md` local-first rules |
| Out of scope | XMP / HEIC / RAW / models; desktop installer-shell redo; D3.06 tray; merging [PR #41](https://github.com/joe-cheung-cae/frame-pilot/pull/41); version bump; production-code fixes |

### Surfaces reviewed

- `apps/desktop` — Tauri 2 / Vite / Rust lifecycle (`sidecar.rs`, `lib.rs`, `menu.rs`, `data_dir.rs`), `tauri.conf.json`, capabilities, native FS adapter, router, theme CSS
- `packaging/` — PyInstaller one-dir spec, `build.sh`, `stage-sidecar.sh`, `scripts/sidecar-smoke.sh`
- Desktop-related API — `sidecar_main.py`, `origins.py` / Host middleware, path import, project-root registry, `GET /api/meta`, Phase 6 reclaim (`jobs.py`, `main.py` lifespan, `worker.py`)
- Shared `apps/web` — `shell.ts`, `apiBase.ts`, `StatusBar`, `SettingsPanel`, `Shell`, navigation adapter, ImportPanel / ExportPanel desktop branches

### Explicitly not treated as new gaps

| Item | Why |
| ---- | --- |
| Dated GUI `[x]` close-outs for D0.07, D1.08, D3.01–D3.04 | Recorded in the packaging tracker with rustc 1.98.0 / live WebView evidence; this review did not re-open a GUI |
| D3.06 tray `[-]` | Deferred 2026-08-28; D5.05 already records it; no `fs:` / `shell:` tray capabilities |
| Unsigned NSIS/DMG | Accepted RC posture (`docs/desktop_signing.md`, D5.05) |
| `GET /api/meta` loopback `data_dir` | Intentional D3.03 Settings surface; Host-checked |
| 500-photo GUI RSS unmeasured | Documented pending in D5.03 / performance baseline |
| [PR #41](https://github.com/joe-cheung-cae/frame-pilot/pull/41) | Closed, not merged, superseded by #45; this review did not merge it |

## 3. Safety red lines

| Red line | Shipped result | Hits in this review? |
| -------- | -------------- | -------------------- |
| Original photos must not be modified or deleted | Path import opens sources `rb` and writes copies under `originals/` via `_copy_file_to_path`; immutability tests assert size / mtime / SHA-256; reclaim rewrites job/derivative/group rows only | **No** |
| Bind only `127.0.0.1` | CLI exit 2 for `0.0.0.0` / LAN hosts; bind remaps `localhost` → `127.0.0.1`; Tauri always passes `--host 127.0.0.1`; ready-line host must match | **No** |
| No cloud | No updater plugin, no login/payment/telemetry, no remote processing; Help About has no updater | **No** |
| No wide allowlist | Default `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` is empty; Tauri never sets it; D2.00 registration is the widen path. Residual: API will honor a mis-set env (Finding M1) | **No at default** (see M1) |

## 4. Findings by severity

### 4.1 Medium

| ID | Path | Finding | Safety red line |
| -- | ---- | ------- | --------------- |
| **M1** | `apps/api/app/core/config.py:34-44`, `apps/api/app/services/projects.py:30-35` | Env allowlist accepts `$HOME` / `/` / drive roots with no API rejection | **No at default.** Would void the “no wide allowlist” control **if** an operator exported a broad parent. Tauri does not set the variable. |
| **M2** | `apps/desktop/src-tauri/capabilities/default.json:3-11` | `opener:default` is wider than reveal-in-folder IPC | **No** |
| **M3** | `scripts/sidecar-smoke.sh:32`, `packaging/pyinstaller/framepilot-api.spec:13-21`, `apps/api/app/sidecar_main.py:62-69` | Frozen Windows sidecar health is not proven independently of `PYTHONPATH`; spec omits `uvicorn.loops.asyncio` while Windows forces that loop | **No** (availability / packaging verification) |

#### M1 — Allowlist env is not rejected when set wide

**Evidence.** `get_settings()` splits `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` on `os.pathsep`, expands/resolves each entry, and stores them with no `$HOME` / filesystem-anchor / drive-root filter:

```python
allowlist_raw = os.getenv("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST", "")
# ...
allowlist.append(Path(cleaned).expanduser().resolve())
```

`create_project` then treats those entries as allowed parents (`projects.py:30-35`). Default is `[]`. Registration (`project_roots.py`) **does** block `/`, drive roots, Windows `\Windows`, and `data_dir` plus its parents — but that filter is not applied to the env allowlist.

**Plan.** Packaging locked decision 11 and “What Not To Do” say the allowlist must never be `$HOME`, `/`, or a drive root **by the Tauri shell**. Tauri spawn (`sidecar.rs:467-477`) sets `FRAMEPILOT_DESKTOP=1` and does **not** set the allowlist (confirmed: no `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` assignment under `apps/desktop`). D2.00’s own text already warns that setting the env to `$HOME` voids the control.

**QA re-check.** `rg FRAMEPILOT_PROJECT_ROOT_ALLOWLIST apps/desktop apps/api/app/core/config.py`. Confirm `test_create_project_rejects_root_outside_allowlist` still exists and stays green. Optional: `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME` then `POST /api/projects` with a home-relative `root_path` currently succeeds — that is the gap, not a shipped default.

**Suggested follow-up (not in this PR):** reject env entries that are `$HOME`, `/`, a drive root, or other blocked names using the same helpers as `register_root`.

#### M2 — `opener:default` is wider than reveal-in-folder

**Evidence.** Capabilities:

```json
"permissions": [
  "core:default",
  "core:window:allow-show",
  "core:window:allow-unminimize",
  "core:window:allow-set-focus",
  "window-state:default",
  "dialog:default",
  "opener:default"
]
```

There are **no** `fs:allow-*` or `shell:allow-open` permissions (D3.06 tray correctly added none). Frontend only calls `revealItemInDir` (`apps/desktop/src/lib/nativeFs.ts:45-46`; menu Open data folder in `menu.rs:128-131`). `opener:default` is the plugin’s full default set, which typically also allows open-url / open-path, not a reveal-only allowlist.

**Plan.** Locked decision 4 / D2.01: optional Tauri IPC for dialogs, paths, and reveal-in-folder only. CSP `script-src 'self'` reduces XSS reach; this is least-privilege, not a bind/cloud/originals break.

**QA re-check.** Read `apps/desktop/src-tauri/capabilities/default.json`. `rg "fs:|shell:" apps/desktop/src-tauri` should stay empty of filesystem/shell capabilities.

**Suggested follow-up (not in this PR):** replace `opener:default` with a reveal-scoped permission list.

#### M3 — Frozen sidecar smoke can hide Windows loop/import gaps

**Evidence.**

1. `sidecar_main.serve` forces `loop="asyncio"` on Windows (`sidecar_main.py:62-69`) because uvloop may be absent.
2. `framepilot-api.spec` hiddenimports list `uvicorn.loops.auto` but **not** `uvicorn.loops.asyncio` (or `uvicorn.protocols.http.httptools_impl`). `hook-app.py` only `collect_submodules("app")`.
3. `scripts/sidecar-smoke.sh:32` always `export PYTHONPATH="$repo_root/apps/api..."`, including when the process under test is the frozen `dist/framepilot-api/framepilot-api[.exe]`. Packaged Tauri spawn **removes** `PYTHONPATH` (`sidecar.rs:474-477`).
4. `packaging/pyinstaller/build.sh` runs that smoke after the freeze; `.github/workflows/desktop.yml` builds NSIS/DMG but does **not** launch the packaged app.

**Plan.** D0.05 requires hiddenimports sufficient for `/health` after start. D1.04 production spawn must not inherit a parent `PYTHONPATH` that shadows bundled imports — Rust does that; the smoke script does not match production.

**QA re-check.** Diff smoke env vs `spawn_sidecar`. On a Windows host: freeze, `env -u PYTHONPATH dist/framepilot-api/framepilot-api.exe --host 127.0.0.1 --port 0 --data-dir <abs>`, parse ready line, `GET /health`.

**Suggested follow-up (not in this PR):** add `uvicorn.loops.asyncio` (and the http impl modules actually imported) to the spec; stop exporting `PYTHONPATH` when invoking the frozen binary.

### 4.2 Low

| ID | Path | Finding | Safety red line |
| -- | ---- | ------- | --------------- |
| **L1** | `apps/desktop/src-tauri/src/sidecar.rs:467-477` | Spawn does not `env_remove("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST")`; a parent `tauri dev` shell could leak a wide allowlist into the sidecar | **No** (Tauri does not set it; pairs with M1) |
| **L2** | `apps/api/app/core/project_roots.py:11`, `108-125` | `register_root` does not reject `Path.home()` by name. Packaged macOS/Windows usually block it because `data_dir` lives under home (`_is_data_dir_or_parent`). Linux/WSL **dev** uses repo `.framepilot-desktop-dev`, so registering `$HOME` can succeed. **Follow-up:** [#138](https://github.com/joe-cheung-cae/frame-pilot/issues/138) — `register_root` now rejects the current home directory by name. | **No** for packaged OS app-support; **partial** for Linux desktop-dev (closed by #138) |
| **L3** | `apps/desktop/src/lib/nativeFs.ts:75-77` vs `apps/web/src/lib/nativeFs.ts:10-12` | Desktop `getNativeFs()` always returns the adapter object, never `null`. D2.01 browser-null is the web stub. A non-Tauri open of desktop Vite can take native-picker branches and then fail plugin calls. **Follow-up:** [#140](https://github.com/joe-cheung-cae/frame-pilot/issues/140) — desktop `getNativeFs()` now returns `null` when not running in Tauri. | **No** (closed by #140) |
| **L4** | `apps/desktop/src/lib/nativeFs.ts:1`, `apps/desktop/package.json` | Imports `@tauri-apps/api/webview` without a direct dependency (transitive via plugins). **Follow-up:** [#142](https://github.com/joe-cheung-cae/frame-pilot/issues/142) — `apps/desktop/package.json` now lists `@tauri-apps/api` as a direct dependency covering `@tauri-apps/api/webview`. | **No** (closed by #142) |

### 4.3 Notes (below bar / already documented)

| ID | Path | Note | Safety red line |
| -- | ---- | ---- | --------------- |
| N1 | `apps/api/app/api/meta.py:10-12` | `GET /api/meta` returns absolute `data_dir`. Host middleware still applies. Same-machine loopback disclosure; D3.03 by design. Phase 5 review already logged this below bar | No |
| N2 | `apps/api/app/sidecar_main.py:84`, `{data_dir}/logs/sidecar.log` | Ready line and sidecar log include `data_dir`. Same-user local visibility | No |
| N3 | `apps/web/src/lib/api.ts` (`export const API_BASE`) | Frozen export remains; `request` / `assetUrl` / `exportDownloadUrl` call `resolveApiBase()` at call time (D1.02). Residual footgun only for future readers of `API_BASE` after late injection | No |
| N4 | `apps/desktop/src-tauri/src/sidecar.rs:289-296` | Loopback port is allocated, listener dropped, then `--port <n>` is passed (TOCTOU). Plan D1.04 specifies this; ready-line port mismatch fails fast; never `--port 0` on the shipped path | No |
| N5 | `apps/desktop/src-tauri/tauri.conf.json` `withGlobalTauri` | Needed for quit-dialog `window.__TAURI__.event.emit`. Widens the page IPC surface vs invoke-only | No |
| N6 | `apps/desktop/src-tauri/src/sidecar.rs` quit overlay CSS | Hardcoded `#fff` / system-ui, not `--fp-*` tokens. D3.04 shell theme itself is implemented | No |
| N7 | `apps/api/app/core/config.py:32-33` | Non-sidecar `get_settings()` still falls back to CWD `.framepilot-data`. Sidecar `--data-dir` is required and applied before `import app.main` | No for sidecar |
| N8 | `.github/workflows/desktop.yml` | CI uploads unsigned NSIS/DMG; does not launch the packaged GUI. Documented | No |
| N9 | `apps/web/src/components/ExportPanel.tsx` | Browser download is `<a href={exportDownloadUrl(...)}>` without the HTML `download` attribute. Desktop uses reveal (`isDesktopShell()`). Not a WebView-download regression | No |

## 5. Areas reviewed (clear)

| Area | Result |
| ---- | ------ |
| Sidecar CLI (D0.01) | `--host` must be `127.0.0.1` or `localhost` (exit 2 otherwise); `--data-dir` required and absolute; `FRAMEPILOT_DATA_DIR` set before `import app.main`; bind IPv4 loopback; POSIX `SO_REUSEADDR` only (`os.name != "nt"`); ready line stdout `flush=True` from `getsockname()`; uvicorn logs on stderr; FastAPI object passed to `Server` |
| Health (D0.02) | `/health` and `/api/health` return `status` / `version` (`APP_VERSION`) / `service` |
| Origin + Host (D0.03) | Host check on **all** methods including GET; missing Host rejected; mutating Origin allowlist; no CORS `*`; desktop origins only if `FRAMEPILOT_DESKTOP=1` (`origins.py`, `main.py:117-131`; `test_desktop_origins.py`) |
| Path import (D0.04) | Absolute paths; `os.walk(..., followlinks=False)`; caps 5000/20000; skip sources under project root; chunk 100 + `remaining_paths`; `source.open("rb")` → `register_import_file` → `_copy_file_to_path` `wb` to dest only; `test_import_from_paths_immutability.py` |
| Project roots (D2.00 / D2.07) | Endpoints 404 unless desktop env; registry `{data_dir}/desktop_project_roots.json` cap 50; `test_create_project_rejects_root_outside_allowlist` present |
| Data dir (D1.05) | Packaged: macOS Application Support / Windows `%APPDATA%\FramePilot` / Linux `~/.local/share/FramePilot`; dev: `.framepilot-desktop-dev`; packaged rejects CWD `.framepilot-data` filename |
| Lifecycle (D1.04 / D1.09 / J6.07) | Allocate loopback port, inject `__FRAMEPILOT_API_BASE__` + `__FRAMEPILOT_DESKTOP__ = true`; crash: one restart then blocking error; close/Cmd+Q share `app_quit_action` → dialog; import can cancel-then-SIGTERM; processing has no cancel; reclaim-aware copy; `interrupted` treated terminal while waiting on cancel; window Destroyed/Exit stops sidecar |
| Menu (D3.01 / D3.07) | File/Edit/View/Project/Help; accelerators only `CmdOrCtrl+N/W/Q`; no bare P/M/X/U; About uses `CARGO_PKG_VERSION`; no updater |
| Status bar (D3.02) | Desktop-only; `Shell` passes `usePathname()`; jobs key `["jobs", projectId]`; no `window.location` / `menuRoutes` |
| Settings (D3.03) | Read-only data dir; “Open data folder” on desktop only; changing data dir not offered |
| Theme (D3.04) | Token swap only under `html[data-shell="desktop"]` + `prefers-color-scheme: dark`; browser stays light |
| Shared navigation (D1.01) | Components import `@/lib/navigation` only; Vite aliases `navigation.next` → `navigation.router.tsx`; no `next/link` in `apps/web/src/components` |
| API base (D1.02 / D1.02a) | `resolveApiBase()` window → env → `http://127.0.0.1:8000`; `isDesktopShell()` is `=== true` only |
| Import / export UI (D2.03 / D2.09) | Desktop path import + remaining-paths loop; browser `<input type="file">` + `webkitdirectory` kept when `!desktopShell`; desktop reveal vs browser download href |
| CSP (D0.07) | Matches locked CSP: `default-src 'self'`; loopback `img-src`/`connect-src`; `object-src 'none'`; `frame-ancestors 'none'` |
| Bundle (D4.01 / D4.02) | `targets: ["nsis","dmg"]`; identifier `com.framepilot.app`; resources one-dir `framepilot-api` (not `externalBin`); artifact-check exception still `^apps/desktop/src-tauri/icons/[^/]+\.(png\|ico\|icns)$` |
| Phase 6 reclaim | `job_reclaim_on_startup` default `True` (`config.py`); `reconcile_active_jobs_on_startup` in `ensure_db_ready`; `start_reclaimable_jobs` in lifespan **not** `GET /api/projects` (`routes.py:331-337` says read-only); export still fail-and-cleanup; lease claim avoids double-run with `python -m app.worker` (#104); originals not rewritten |
| Cloud / updater | `Cargo.toml` has window-state, single-instance, dialog, opener only — no updater plugin |

## 6. Plan alignment snapshot

| Source | Alignment |
| ------ | --------- |
| Packaging Phases 0–5 tracker | All required ids `[x]` or deferred `[-]` (D3.06, D4.03). GUI `[x]` close-outs dated 2026-08-31 |
| Locked decisions 1–16 | Hold, with M1/M2/M3 residual gaps above |
| Phase 6 J6.01–J6.08 + 6.1 default-on | Landed; J6.07 quit copy matches reclaim default; GET list stays free of reclaim writes |
| `AGENTS.md` red lines | Originals / bind / cloud hold; allowlist holds at default (M1 residual) |

## 7. Recommendation

1. Rebase-merge **this docs-only review PR**. Do not start production fixes until that merge.
2. After merge, a separate implementer PR can take M1–M3 (allowlist rejection, opener scope, frozen-smoke `PYTHONPATH` + `uvicorn.loops.asyncio`).
3. Do **not** reopen D3.06 tray, redo the installer shell, bump the version, implement XMP, or merge PR #41 (already closed).
4. Before any **public signed** release, keep D4.05 / D5.05 unsigned-installer language and signing runbook as the gate (already documented; not a new gap here).

---

Generated 2026-09-01 against `011fb61c745cf0eaac103ec3998db46095ace1cf` for issue #118. No production-code changes.
