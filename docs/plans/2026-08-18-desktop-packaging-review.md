# Opus 5 Review: Desktop Packaging Plans

> **Reviewer:** Claude Opus 5  
> **Date:** 2026-08-18  
> **Scope:** `docs/desktop_development_plan.md`, `docs/plans/2026-08-18-desktop-packaging.md`, `docs/desktop_goal_mode.md` vs live `2.0.0-rc2` tree  
> **Verdict:** Product direction is sound. The first executable backlog was **not** safe to hand to Goal Mode until the 2026-08-18 refinement. After applying this review, Goal Mode may start at **D0.00**.

---

## Verdict

Tauri 2 plus a PyInstaller sidecar is the right wrap for an app that already speaks local HTTP. The first backlog named real files and protected the browser app, but six defects would each burn hours or produce a wrong-but-green commit:

1. `--port 0` could not report the bound port the way D0.01 specified (`uvicorn.run` blocks before the port is known).
2. The navigation-adapter sample imported a non-existent module and named a `.test.ts` file that this repo’s runners would not collect.
3. Vite had no `@` alias or PostCSS/Tailwind story, so the first desktop build would fail.
4. Tauri PNG icons would fail `npm run verify` via `scripts/check-release-artifacts.sh`.
5. A native folder picker cannot produce a legal `root_path` under `projects.py` allowlist rules, and non-empty folders also 422 without `acknowledge_nonempty`.
6. A folder of 2000 photos had no defined request shape against `IMPORT_MAX_FILES_PER_REQUEST = 100`.

Two structural gaps: no per-task tracker, and no definition of “done” when WSL cannot open a WebView.

**Human decision locked in the refined plan:** keep custom project roots for 2.1 via a desktop-only root-registration endpoint (D2.00). Forbidding custom roots would be smaller, but photographers with a large photo drive and a small system disk need it.

---

## Severity summary

### Critical (would fail Goal Mode or shipping)

| ID | Issue | Where |
|----|--------|--------|
| A1.1 | Product plan still said “try Next export / maybe migrate `apps/web`”; backlog locked dual-shell Vite | product §3.3 vs impl §2 |
| A1.2 | Product Phase 0 required dual-platform GUI; this machine is WSL2 | product §6 vs impl env note |
| A2.1 | Sidecar `--port 0` ready-line is unimplementable as first written | D0.01 |
| A2.3 | Native picker vs project-root allowlist + nonempty ack | D2.02, `projects.py:33-43` |
| A2.4 | Path import vs 100-file cap / sync copy of 2000 files | D0.04, `importing.py:43` |
| A2.6 | Invalid navigation adapter + unrunnable test path | D1.01, `package.json` test split |
| A2.7 | Missing Vite `@` alias, Tailwind v3 PostCSS, `globals.css` | D1.03 |
| A2.9 | Tauri icons fail `check:artifacts` | `scripts/check-release-artifacts.sh` |

### Important

- Version `2.1.0` vs `3.0.0` vs `2.1.0-desktop` not locked in the product plan
- Product §5 UI (detached preview, concurrency knobs, updater) not deferred
- Module-level `create_app()` vs CWD-relative data dir
- Mixed content / WKWebView download anchors
- Incomplete PyInstaller hiddenimports (lifespan/websocket)
- `apps/desktop` missing from `install:all` / `verify`
- D4.03 “can land earlier” unreachable under sequential loop
- DNS rebinding: GET routes have no Host check
- No graceful quit while a job runs
- No per-task checkbox tracker; GUI-blocked “done” undefined
- Playwright `ImportPanel` file inputs must stay for browser E2E

### Minor

- Linux data dir missing from product §3.4
- `packaging/scripts/` in D4.01 but not the tree
- `.gitignore` missing `target/`
- Health test exact-equality not named in D0.02
- Several tasks had no Tests field

---

## In scope for 2.1.0-desktop vs deferred

| Item | 2.1 |
|------|-----|
| Native menus, window state, dialogs, drag-drop, reveal in folder | In |
| Status bar, existing keyboard shortcuts, virtual lists (already shipped) | In |
| System theme (desktop-scoped), read-only data-dir display | In |
| Detached preview window | Defer 2.2 |
| Concurrency/cache settings | Defer 2.2 (backend is sequential) |
| Auto-update / check for updates | Defer 2.2 |
| System tray | Optional D3.06, else 2.2 |
| Changing the data directory | Defer 2.2 |

---

## What changed after this review

Applied into:

- `docs/desktop_development_plan.md` (v1.2)
- `docs/plans/2026-08-18-desktop-packaging.md`
- `docs/desktop_goal_mode.md`

Notable backlog splits: D0.00 (CI first), D0.04a/b/c, D0.07a, D1.02a, D1.03a/b, D1.09, D2.00, D2.09.
