# Desktop Phase 1 Handoff Status

- current_stage: 开发
- status: in_progress
- files changed:
  - D1.01 navigation adapter (`a5bffba`)
  - D1.02 runtime API base (`cdc3423`); §5.1 D1.02 `[x]`
  - D1.02a desktop shell flag (`fabe7a1`); §5.1 D1.02a `[x]`
  - D1.03a Vite build, aliases, Tailwind; §5.1 D1.03a `[x]`
  - D1.03b desktop router (`616fea3`): `apps/desktop/src/router.tsx`, `navigation.router.tsx` (`href` → `to`, drop `prefetch`), `App.tsx`; routes match `apps/web/src/app`; shared `HelpShortcuts`; Next help page keeps metadata; Vite entry replaced Phase 0 `index.html` / `health.js`
  - §5.1 D1.03b `[x]`
- tests_run: `npm run typecheck:desktop`; `npm --prefix apps/desktop run build` (CSS 14.20 kB); `npm run test:web` (181 node:test + 8 vitest + `next build`, exit 0)
- next_stage: 开发
- blockers: none (D0.07 rustc still [~] is inherited)
- branch: feature/desktop-packaging
- timestamp: 2026-08-19

开发 in progress. D1.03b desktop router is landed and §5.1 D1.03b is `[x]`. React Router reuses the shared web page components (`ProjectList`, `HelpShortcuts`, `SettingsPanel`, `ProjectCreator`, `ProjectDashboard`, `ImportPanel`, `ProcessingPanel`, `CullingWorkspace`, `ExportPanel`) with the same `QueryClientProvider` as `Providers.tsx`. The desktop entry calls `applyShellDataset()`. Vite does not import Next `page.tsx` files. Remaining Phase 1 boxes stay `[ ]` until their commits. Do not start D1.04 in this handoff.

Phase 0 remains closed GO on `origin/main` (`1d6ffa7`). D0.07 `[~]` rustc/cargo/rustup missing as of 2026-08-19T08:26:40Z (`command not found`, exit 127).
