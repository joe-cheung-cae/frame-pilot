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
