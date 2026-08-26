let meta = #{
    name: "d3-02-status-bar",
    description: "Investigate, plan, implement, and verify FramePilot D3.02 status bar (issue 46)",
    when_to_use: "Land GitHub issue 46 / task D3.02 Status bar on feature/d3-02-status-bar without pushing or opening a PR",
    phases: [
        #{ title: "Investigate", detail: "Read spec, live Shell, processingProgress, health, and desktop shell flag" },
        #{ title: "Plan", detail: "Tests-first D3.02 plan from live evidence" },
        #{ title: "Implement", detail: "Failing tests, desktop status bar, tracker tick, local commit" },
        #{ title: "Verify", detail: "Run named tests, review diff, confirm D3.03+ untouched" },
    ],
};

fn notes_schema() {
    #{
        "type": "object",
        "required": ["notes"],
        "properties": #{
            "notes": #{ "type": "string" },
        },
    }
}

fn plan_schema() {
    #{
        "type": "object",
        "required": ["ok", "notes"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "tests_first": #{ "type": "string" },
            "files": #{ "type": "string" },
            "sidecar": #{ "type": "string" },
            "gui": #{ "type": "string" },
            "notes": #{ "type": "string" },
        },
    }
}

fn stage_schema() {
    #{
        "type": "object",
        "required": ["ok", "notes"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "commit": #{ "type": "string" },
            "files_changed": #{ "type": "string" },
            "tests_run": #{ "type": "string" },
            "skipped": #{ "type": "string" },
            "notes": #{ "type": "string" },
        },
    }
}

fn verify_schema() {
    #{
        "type": "object",
        "required": ["ok", "passed", "files_changed", "tests_run", "skipped", "notes"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "passed": #{ "type": "boolean" },
            "commit": #{ "type": "string" },
            "files_changed": #{ "type": "string" },
            "tests_run": #{ "type": "string" },
            "skipped": #{ "type": "string" },
            "notes": #{ "type": "string" },
        },
    }
}

fn repo_rules() {
    let s = "";
    s += "Repo: resolve with git rev-parse --show-toplevel. This checkout is /workspace/frame-pilot-d302.\n";
    s += "Branch must stay feature/d3-02-status-bar (from main SHA 0d0b304aaaf2c67db7a29d4bbb6e4f473d75b38b).\n";
    s += "Do not checkout main. Do not merge. Do not git push. Do not open a GitHub PR. Do not squash. Do not force-push.\n";
    s += "Leave PR #41 unmerged. Do not change remotes or git config. Do not run git config --global or git config user.name.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, docs, commits, and new UI strings. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP.\n";
    s += "ONE TASK ONLY: D3.02 Status bar and processing visibility (GitHub issue 46). Do not implement D3.03, D3.04, D3.05, D3.06, or D3.07.\n";
    s += "Do not start Phase 4 or Phase 5. Do not bump APP_VERSION. It must stay 2.0.0-rc2 in apps/api/app/core/version.py, package.json files, and tauri.conf.json.\n";
    s += "Do not add GET /api/meta (that is D3.03). Do not extend GET /health or GET /api/health payloads. Do not add a tray (D3.06). Do not add system theme follow (D3.04). Do not rewrite empty/error copy (D3.05). Do not rewrite Help accelerators (D3.07).\n";
    s += "Do not overwrite bilingual living pages, MIT LICENSE, or docs/desktop_goal_mode.md / docs/desktop_goal_mode.zh.md. Do not rewrite the desktop packaging plan body; only tick the §5.1 D3.02 tracker line.\n";
    s += "Do not set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME, /, or a drive root.\n";
    s += "Do not migrate apps/web off Next.js. Do not add output: export.\n";
    s += "Do not add fs: or shell: capabilities.\n";
    s += "npm run verify must not install or require rustc, cargo, or Tauri.\n";
    s += "Do not add Co-authored-by Cursor or similar trailers.\n";
    s += "If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>' (Joe Cheung <60860967+joe-cheung-cae@users.noreply.github.com>).\n";
    s
}

fn d302_spec() {
    let s = "";
    s += "Spec (authoritative): docs/plans/2026-08-18-desktop-packaging.md section ### D3.02 — Status bar and processing visibility and §5.1.\n";
    s += "Depends on: D3.01, D1.02a. D3.01 is already on this main-based branch as [~].\n";
    s += "Files: desktop-only status bar or Shell.tsx gated by isDesktopShell().\n";
    s += "Show sidecar connected, project name, job step/percent. Reuse apps/web/src/lib/processingProgress.ts. Keep the browser shell unchanged if possible.\n";
    s += "Tests: helper/render test when isDesktopShell() is true. Run: npm run test:web.\n";
    s += "Commit subject (exact): desktop: add status bar for sidecar and jobs\n";
    s += "Tick D3.02 in §5.1 in the SAME commit as the implementation. Do not tick D3.03-D3.07. Do not tick Phase 3 acceptance boxes.\n";
    s += "If GUI/WebView cannot be recorded, tick D3.02 [~] and append a dated command+error note in docs/desktop_feasibility_notes.md (and the matching .zh.md append, without rewriting existing sections). If unit tests pass and a GUI run was recorded, tick [x]. Never leave the box [ ].\n";
    s
}

fn inspect_prompt() {
    let s = "";
    s += "You are grok-4.6 investigating FramePilot D3.02 Status bar. Read-only. Do not edit. Do not commit.\n";
    s += repo_rules();
    s += d302_spec();
    s += "Use grep/read_file/list_dir. Read at least:\n";
    s += "- docs/plans/2026-08-18-desktop-packaging.md D3.02, D1.02a isDesktopShell, §2 locked decisions, §5.1 Phase 3 boxes\n";
    s += "- docs/desktop_goal_mode.md WSL/GUI and test-first rules for D3.02\n";
    s += "- apps/web/src/components/Shell.tsx (no status bar yet)\n";
    s += "- apps/web/src/lib/shell.ts, shell.test.ts, processingProgress.ts, processingProgress.test.ts\n";
    s += "- apps/web/src/lib/api.ts (no getHealth yet; listJobs/getProject exist), apiBase.ts\n";
    s += "- apps/web/src/lib/menuRoutes.ts projectIdFromPathname, recentProjects.ts loadLastOpenedProjectId\n";
    s += "- apps/web/src/components/ProcessingPanel.tsx job polling pattern\n";
    s += "- apps/web/src/components/Providers.tsx, apps/desktop/src/App.tsx applyShellDataset\n";
    s += "- apps/api/app/core/version.py APP_VERSION and health_payload; apps/api/app/main.py GET /health; apps/api/app/api/routes.py GET /api/health\n";
    s += "- apps/web/package.json test:unit (src/lib/*.test.ts node:test + vitest src/**/*.test.tsx)\n";
    s += "- docs/desktop_feasibility_notes.md D3.01 GUI skip pattern\n";
    s += "Confirm: Shell has no status bar; isDesktopShell is true only for literal true; processingProgress already formats step/percent; health exists and must not grow data_dir; GET /api/meta does not exist.\n";
    s += "notes: a factual brief of live files, gaps, and risks for D3.02 only.\n";
    s
}

fn progress_prompt() {
    let s = "";
    s += "You are grok-4.6 investigating D3.02 processing visibility reuse. Read-only. Do not edit.\n";
    s += "Read apps/web/src/lib/processingProgress.ts and processingProgress.test.ts and ProcessingPanel.tsx.\n";
    s += "List the exact helpers D3.02 must reuse for job type label, status label, progress percent, progress summary, and picking an active job (queued/running, then latest processing job).\n";
    s += "State how ProcessingPanel polls jobs (queryKey, refetchInterval). Status bar should follow that pattern, not invent a second progress formula.\n";
    s += "Do not propose GET /api/meta. Sidecar connected must use existing GET /health or GET /api/health (status === \"ok\").\n";
    s += "notes: reuse table (helper -> status-bar field) and polling approach.\n";
    s
}

fn shell_prompt() {
    let s = "";
    s += "You are grok-4.6 investigating D3.02 shell gating and render tests. Read-only. Do not edit product files.\n";
    s += "Read Shell.tsx, shell.ts, shell.test.ts, a representative component test (ProcessingPanel.test.tsx or ProjectDashboard.test.tsx), apps/web/src/app/page.tsx, apps/desktop/src/router.tsx.\n";
    s += "Explain how to keep the browser shell unchanged: StatusBar returns null unless isDesktopShell() is true; do not inline window.__FRAMEPILOT_DESKTOP__ checks; consume isDesktopShell() / [data-shell=desktop].\n";
    s += "Shell is imported from Next.js server pages; keep Shell itself free of hooks if possible and put hooks in a client StatusBar.tsx with \"use client\".\n";
    s += "Do not add usePathname to the navigation adapter (out of D3.02). Resolve project id from window.location.pathname via projectIdFromPathname then loadLastOpenedProjectId; re-read on the same poll interval as health/jobs so SPA navigations update.\n";
    s += "Render tests: set window.__FRAMEPILOT_DESKTOP__ to true vs not-true; assert a status region appears only when true; header Help/Settings/New Project stay.\n";
    s += "notes: gating, file split, and render-test strategy.\n";
    s
}
