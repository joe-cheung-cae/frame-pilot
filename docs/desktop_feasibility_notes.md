# Desktop Feasibility Notes

Phase 0 measurements and blockers for FramePilot desktop packaging. Drafted during `开发` on 2026-08-19. `上线` owns the final go/no-go and `docs/plans/2026-08-18-desktop-packaging.md` §5.1 ticks.

This host is **macOS**, not WSL2.

## Blockers

### D0.07 Tauri GUI / Rust toolchain `[~]` — 2026-08-19

Commands and exact errors:

```text
$ cargo --version
zsh: command not found: cargo

$ rustc --version
zsh: command not found: rustc

$ command -v rustup || echo "rustup not found"
rustup not found
```

Captured from this workspace shell on 2026-08-19:

```text
(eval):1: command not found: cargo
(eval):1: command not found: rustc
rustup not found
```

No system Rust toolchain was installed. `npm run verify` does not invoke `cargo`, `rustc`, or Tauri. A verify-safe skeleton lives under `apps/desktop/` (blank HTML health probe, locked CSP in `src-tauri/tauri.conf.json`, sidecar spawn notes in `src-tauri/src/lib.rs`). Sidecar smoke was run without a WebView.

Until a dated `cargo`/`WebView` run succeeds, D0.07 stays `[~]`.

## D0.06 — Next.js `output: 'export'` spike

Attempted a throwaway change to `apps/web/next.config.ts`:

```ts
output: 'export',
```

`npm --prefix apps/web run build` compiled, then failed:

```text
Error: Page "/projects/[projectId]/cull" is missing "generateStaticParams()" so it cannot be used with "output: export" config.
```

Current App Router pages under `apps/web/src/app/projects/[projectId]/` with no `generateStaticParams`:

- `page.tsx`
- `cull/page.tsx`
- `export/page.tsx`
- `import/page.tsx`
- `process/page.tsx`

`CullingWorkspace.tsx` calls `useSearchParams()` from `next/navigation`. The export build never reached a full static emit, so Suspense warnings for `useSearchParams` were not observed on this run. They remain a known Next 15 App Router issue if export were forced later.

The throwaway `output: 'export'` line was **reverted** in the same work. `apps/web` stays Next.js. Locked follow-up remains a Vite SPA in `apps/desktop` (Phase 1). No frontend migration was started.

## Baselines

Recorded 2026-08-19 on this macOS host, venv sidecar (`PYTHONPATH=apps/api .venv/bin/python -m app.sidecar_main --host 127.0.0.1 --port 0 --data-dir <tmp>`).

| Measurement                            | Result                                                                |
| -------------------------------------- | --------------------------------------------------------------------- |
| Ready line                             | `FRAMEPILOT_API ready host=127.0.0.1 port=<ephemeral> data_dir=<tmp>` |
| `GET /health` body                     | `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}`    |
| Time to ready + `/health`              | 0.703 s (ready ~0.663 s, curl ~0.040 s)                               |
| Sidecar RSS after `/health`            | 98320 KB (~96 MB)                                                     |
| PyInstaller `dist/framepilot-api` size | not built on this host (smoke used `.venv` module)                    |
| Tauri hello RSS                        | blocked on missing rustc/WebView                                      |
| `imagehash`                            | 4.3.2 present                                                         |
| `numpy`                                | 2.5.2 present                                                         |
| `scipy`                                | 1.18.0 present                                                        |
| `pywt` (PyWavelets)                    | 1.8.0 present                                                         |

`scripts/sidecar-smoke.sh` passed: ephemeral `--data-dir`, `--port 0`, parsed ready line, curled `/health` for `version`, SIGTERM, process exited within 5 s.

## Go / no-go (draft)

`上线` owns the final wording. Draft from `开发`:

- **Shell:** stay Tauri 2 + Python sidecar. Electron is only in play if a later dated run shows Tauri cannot spawn the sidecar or the WebView cannot reach loopback. This host could not compile or open a Tauri window (`cargo`/`rustc` missing), so that failure mode is not proven.
- **Frontend:** keep `apps/web` on Next.js. Desktop UI follow-up is a Vite SPA (Phase 1). `output: 'export'` is not viable without `generateStaticParams` on the five `projects/[projectId]` routes.
- **Scoring stack:** keep imagehash/scipy/PyWavelets. Unpacked sidecar size was not measured (no PyInstaller dist on this run). Do not drop scipy unless a later unpacked sidecar exceeds 250 MB.
- **API work needed for desktop is in place:** loopback sidecar CLI, health `version`/`service`, origin + Host policy, path import with 100-file chunks, and copy-mode immutability tests.

Phase 1 should not start from this draft.
