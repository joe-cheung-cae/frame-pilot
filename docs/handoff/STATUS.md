# Desktop Phase 1 Handoff Status

- current_stage: 开发
- status: in_progress
- files changed:
  - D1.01 navigation adapter (`a5bffba`)
  - D1.02 runtime API base (`cdc3423`): `apps/web/src/lib/apiBase.ts`, `apps/web/src/types/globals.d.ts`, call-time `resolveApiBase()` in `request` / `assetUrl` / `exportDownloadUrl`
  - `apps/web/src/lib/apiBase.test.ts` and `apps/web/src/lib/api.test.ts` — window, env, default, trailing slash, missing window, call-time injection
  - §5.1 D1.02 `[x]`
- tests_run: `npm run typecheck && npm run test:web` (181 node:test + 8 vitest + `next build`, exit 0)
- next_stage: 开发
- blockers: none (D0.07 rustc still [~] is inherited)
- branch: feature/desktop-packaging
- timestamp: 2026-08-19

开发 in progress. D1.02 runtime API base is landed (`cdc3423`) and §5.1 D1.02 is `[x]`. `resolveApiBase()` order is window `__FRAMEPILOT_API_BASE__`, then `NEXT_PUBLIC_API_BASE_URL`, then `http://127.0.0.1:8000`. Trailing slashes are trimmed. Missing `window` does not throw. `API_BASE` stays exported; `request`, `exportDownloadUrl`, and `assetUrl` resolve at call time. D1.02a code is already on the branch (`fabe7a1`) and is next to tick. Remaining Phase 1 boxes stay `[ ]` until their commits or `上线`.

Phase 0 remains closed GO on `origin/main` (`1d6ffa7`). D0.07 `[~]` rustc/cargo/rustup missing as of 2026-08-19T08:26:40Z (`command not found`, exit 127).
