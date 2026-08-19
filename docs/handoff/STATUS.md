# Desktop Phase 1 Handoff Status

- current_stage: 开发
- status: in_progress
- files changed:
  - D1.01 navigation adapter (`a5bffba`)
  - D1.02 runtime API base (`cdc3423`); §5.1 D1.02 `[x]`
  - D1.02a desktop shell flag (`fabe7a1`): `apps/web/src/lib/shell.ts` `isDesktopShell()` literal-`true` only; `applyShellDataset()` SSR-safe (I3)
  - `apps/web/src/lib/shell.test.ts` — drive shipped helper (N3)
  - `apps/web/src/components/Providers.tsx` — apply browser `data-shell`
  - §5.1 D1.02a `[x]`
  - D1.03a Vite build, aliases, Tailwind (`40a428b`)
  - D1.03b desktop router (`616fea3`)
- tests_run: `npm run typecheck && npm run test:web` (181 node:test + 8 vitest + `next build`, exit 0)
- next_stage: 开发
- blockers: none (D0.07 rustc still [~] is inherited)
- branch: feature/desktop-packaging
- timestamp: 2026-08-19

开发 in progress. D1.02a desktop shell detection is landed (`fabe7a1`) and §5.1 D1.02a is `[x]`. `isDesktopShell()` is true only for `window.__FRAMEPILOT_DESKTOP__ === true` and is false for `undefined`, `"1"`, `0`, or missing `window`. `applyShellDataset()` no-ops without `document` and sets `document.documentElement.dataset.shell` to `desktop` or `browser`. `Providers.tsx` applies the browser dataset. D1.03a (`40a428b`) and D1.03b (`616fea3`) are also on the branch. Remaining Phase 1 boxes stay `[ ]` until their commits or `上线`.

Phase 0 remains closed GO on `origin/main` (`1d6ffa7`). D0.07 `[~]` rustc/cargo/rustup missing as of 2026-08-19T08:26:40Z (`command not found`, exit 127).
