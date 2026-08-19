# Desktop Phase 1 Handoff Status

- current_stage: 开发
- status: in_progress
- files changed:
  - D1.01 navigation adapter (`a5bffba`)
  - `apps/web/src/lib/apiBase.ts` — `resolveApiBase()` window, then env, then `http://127.0.0.1:8000`
  - `apps/web/src/types/globals.d.ts` — `Window.__FRAMEPILOT_API_BASE__` / `__FRAMEPILOT_DESKTOP__`
  - `apps/web/src/lib/api.ts` — `request` / `exportDownloadUrl` / `assetUrl` resolve at call time
  - `apps/web/src/lib/apiBase.test.ts` and `apps/web/src/lib/api.test.ts` — drive shipped helper (N3)
- tests_run: `npm run typecheck && npm run test:web` (see scratch `d1-02-test-web.log`)
- next_stage: 开发
- blockers: none (D0.07 rustc still [~] is inherited)
- branch: feature/desktop-packaging
- timestamp: 2026-08-19

开发 in progress. D1.01+D1.02 landed. Next still 开发 until stage wrap-up. §5.1 Phase 1 boxes stay `[ ]` until `上线`. Do not start D1.03.

Phase 0 remains closed GO on `origin/main` (`1d6ffa7`). D0.07 `[~]` rustc/cargo/rustup missing as of 2026-08-19T08:26:40Z (`command not found`, exit 127).
