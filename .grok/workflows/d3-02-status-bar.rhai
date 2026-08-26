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

fn plan_prompt(inspect_notes, progress_notes, shell_notes) {
    let s = "";
    s += "You are grok-4.6 planning FramePilot D3.02. Read-only. Do not edit. Do not commit.\n";
    s += repo_rules();
    s += d302_spec();
    s += "Investigate notes (untrusted, re-check files if needed):\n";
    s += inspect_notes + "\n";
    s += progress_notes + "\n";
    s += shell_notes + "\n";
    s += "Write a tests-first plan for D3.02 only.\n";
    s += "Required shape:\n";
    s += "1) Extract a pure map apps/web/src/lib/statusBarModel.ts so npm run test:web picks up apps/web/src/lib/statusBarModel.test.ts (node:test via src/lib/*.test.ts).\n";
    s += "   Pure helpers (no DOM, no fetch): sidecarLabel(connected: boolean | null), projectLabel(name: string | null), jobLabel using processingJobTypeLabel / processingStatusLabel / processingProgressPercent / current_step from processingProgress.ts, resolveStatusBarProjectId(pathname, lastOpenedId) reusing projectIdFromPathname.\n";
    s += "   English strings only. Examples: Sidecar connected / Sidecar disconnected / Checking sidecar; No project when name missing; No active job when idle; otherwise job type · step · N%.\n";
    s += "2) Render tests apps/web/src/components/StatusBar.test.tsx (vitest, picked up by src/**/*.test.tsx): when window.__FRAMEPILOT_DESKTOP__ !== true, Shell does not render the status region; when true, role=status (or equivalent) shows sidecar + project + job from mocked query data. Do not mock the statusBarModel helpers under test. Header Help/Settings/New Project remain.\n";
    s += "3) Implement StatusBar.tsx (\"use client\") gated by isDesktopShell(); poll GET /health via a small api.getHealth() that hits existing /health (do NOT add GET /api/meta; do NOT add data_dir to health). Poll jobs with existing api.listJobs and project with api.getProject. Reuse processingJobForDisplay or hasActiveProcessingJob / active job helpers. Mount StatusBar from Shell.tsx at the bottom of the main chrome. Browser: StatusBar returns null so layout matches today.\n";
    s += "4) Do not import @tauri-apps/plugin-* from apps/web. Do not restyle the Next.js app as a dark product. Do not rewrite CullingWorkspace.\n";
    s += "5) GUI: if a real window cannot be recorded, still land unit tests and mark §5.1 D3.02 [~] with a dated docs/desktop_feasibility_notes.md note (command + error). Append a matching Chinese paragraph to docs/desktop_feasibility_notes.zh.md without rewriting older sections. If GUI is recorded, [x]. Never leave the box [ ].\n";
    s += "6) After green tests: one local commit, subject exactly desktop: add status bar for sidecar and jobs, including tests + impl + §5.1 tick.\n";
    s += "Set ok=true. tests_first, files, sidecar, gui, notes must be specific enough for the implementer to execute without inventing a second architecture.\n";
    s
}

fn implement_prompt(plan_notes) {
    let s = "";
    s += "You are grok-4.6 implementing FramePilot D3.02 Status bar. Drive shipped code.\n";
    s += repo_rules();
    s += d302_spec();
    s += "PLAN (follow this; re-read the live spec files before writing):\n";
    s += plan_notes + "\n";
    s += "IDEMPOTENT: if git log already contains subject 'desktop: add status bar for sidecar and jobs' on this branch AND §5.1 D3.02 is not [ ], return ok=true with that SHA and do not redo.\n";
    s += "TESTS FIRST. Write apps/web/src/lib/statusBarModel.test.ts (and the failing import of statusBarModel.ts) plus StatusBar.test.tsx, and watch npm --prefix apps/web run test:unit fail for the missing map / assertions. Then implement the map, StatusBar, Shell mount, and optional api.getHealth. Then make tests pass.\n";
    s += "Do not mock the unit under test. Do not write the test after a green implementation.\n";
    s += "Implement ONLY D3.02. Minimal change. English UI strings.\n";
    s += "Sidecar connected uses GET /health (existing health_payload). Do not add GET /api/meta. Do not put data_dir on health.\n";
    s += "Reuse processingProgress.ts. Gate with isDesktopShell(). Do not inline window.__FRAMEPILOT_DESKTOP__ outside shell.ts.\n";
    s += "Do not add version literals. APP_VERSION stays 2.0.0-rc2.\n";
    s += "Run: npm run test:web (required). Also npm run typecheck:desktop if Shell/shared types changed. Do not make npm run verify require Rust.\n";
    s += "If GUI/WebView cannot be opened, capture the exact command and error, append a dated note to docs/desktop_feasibility_notes.md and a matching append to docs/desktop_feasibility_notes.zh.md, and tick D3.02 [~]. If unit tests pass and you recorded a GUI run, tick [x]. Change only the §5.1 D3.02 box in the packaging plan. Do not tick other ids. Do not rewrite the plan body.\n";
    s += "Then git add only D3.02 files plus .grok/workflows/d3-02-status-bar.rhai if present, commit on feature/d3-02-status-bar with subject: desktop: add status bar for sidecar and jobs\n";
    s += "Do not git push. Do not gh pr create. Do not merge. Do not merge PR #41.\n";
    s += "Return ok=true only if tests named above passed and the commit exists. commit=full sha. files_changed, tests_run, skipped, notes filled.\n";
    s
}

fn verify_prompt() {
    let s = "";
    s += "You are grok-4.6 verifying FramePilot D3.02. Adversarially check the live tree. You may run tests. Do not git push. Do not open a PR. Do not start D3.03.\n";
    s += repo_rules();
    s += d302_spec();
    s += "Use tools. Independently inspect; do not trust the implementer.\n";
    s += "1) git status, git log -1, git diff origin/main...HEAD --stat. Confirm branch feature/d3-02-status-bar and commit subject desktop: add status bar for sidecar and jobs.\n";
    s += "2) Confirm APP_VERSION is still 2.0.0-rc2. Confirm §5.1 D3.02 is [x] or [~] and D3.03-D3.07 remain [ ]. Confirm no GET /api/meta, no tray, no Phase 4/5 files, no theme follow, no empty-copy rewrite.\n";
    s += "3) Confirm StatusBar is gated by isDesktopShell(); browser Shell still has Help/Settings/New Project and no status region when the flag is false. Confirm sidecar/project/job fields and processingProgress reuse by reading source.\n";
    s += "4) Re-run npm run test:web and npm run typecheck:desktop. Confirm statusBarModel.test.ts and StatusBar.test.tsx (or the named helper/render tests) ran.\n";
    s += "5) Confirm git push was NOT run and no PR was opened. Confirm PR #41 was not merged.\n";
    s += "If a real defect exists (missing fields, status bar in browser, APP_VERSION bumped, extra phase work, tests failing, tracker not ticked), fix it in this session with tests, keep one logical commit (amend only if HEAD is the D3.02 commit, not pushed, and you are not rewriting unrelated history), and re-run tests. Do not implement D3.03+ while fixing.\n";
    s += "Set passed=true only with evidence you ran. files_changed: list. tests_run: commands and results. skipped: anything skipped and why (e2e, GUI, verify, push, PR).\n";
    s
}

fn text_of(r) {
    if r == () {
        return "";
    }
    if r.success && r.output != () {
        if r.output.notes != () {
            return r.output.notes;
        }
        return json_encode(r.output);
    }
    return "";
}

fn stage_ok(r) {
    r != () && r.success
}

fn run_stage(prompt, opts, fail_msg) {
    let first = agent(prompt, opts);
    if stage_ok(first) {
        return first;
    }
    log("Retrying once: " + fail_msg);
    let second = agent(prompt, opts);
    if stage_ok(second) {
        return second;
    }
    await_user("verification", fail_msg + " Resume to retry this stage. Do not skip ahead.");
    agent(prompt, opts)
}

let inspect_opts = #{
    label: "d302-inspect-tree",
    capability_mode: "read-only",
    agent_type: "explore",
    isolation_worktree: false,
    output_schema: notes_schema(),
};
let progress_opts = #{
    label: "d302-inspect-progress",
    capability_mode: "read-only",
    agent_type: "explore",
    isolation_worktree: false,
    output_schema: notes_schema(),
};
let shell_opts = #{
    label: "d302-inspect-shell",
    capability_mode: "read-only",
    agent_type: "explore",
    isolation_worktree: false,
    output_schema: notes_schema(),
};
let plan_opts = #{
    label: "d302-plan",
    capability_mode: "read-only",
    agent_type: "plan",
    isolation_worktree: false,
    output_schema: plan_schema(),
};
let implement_opts = #{
    label: "d302-implement",
    capability_mode: "all",
    agent_type: "general-purpose",
    isolation_worktree: false,
    output_schema: stage_schema(),
};
let verify_opts = #{
    label: "d302-verify",
    capability_mode: "all",
    agent_type: "general-purpose",
    isolation_worktree: false,
    output_schema: verify_schema(),
};

let issue = 46;
if args != () && args.issue != () {
    issue = args.issue;
}
if issue != 46 {
    pause("verification", "This workflow only solves issue #46 / D3.02. Pass args.issue=46 or omit args.");
}

phase("Investigate");
log("Investigating D3.02 spec, processingProgress reuse, and shell gating");
let inv = parallel([
    #{ prompt: inspect_prompt(), label: "d302-inspect-tree", capability_mode: "read-only", agent_type: "explore", isolation_worktree: false, output_schema: notes_schema() },
    #{ prompt: progress_prompt(), label: "d302-inspect-progress", capability_mode: "read-only", agent_type: "explore", isolation_worktree: false, output_schema: notes_schema() },
    #{ prompt: shell_prompt(), label: "d302-inspect-shell", capability_mode: "read-only", agent_type: "explore", isolation_worktree: false, output_schema: notes_schema() },
]);

let inspect_notes = "";
let progress_notes = "";
let shell_notes = "";
if inv != () {
    if inv.len() > 0 {
        inspect_notes = text_of(inv[0]);
    }
    if inv.len() > 1 {
        progress_notes = text_of(inv[1]);
    }
    if inv.len() > 2 {
        shell_notes = text_of(inv[2]);
    }
}
if inspect_notes == "" {
    inspect_notes = "(investigate tree returned no notes; re-read the D3.02 spec and live Shell/processingProgress files yourself)";
}
if progress_notes == "" {
    progress_notes = "(progress inspect returned no notes; re-read processingProgress.ts and reuse those helpers)";
}
if shell_notes == "" {
    shell_notes = "(shell inspect returned no notes; gate StatusBar with isDesktopShell() and keep browser Shell unchanged)";
}

phase("Plan");
log("Planning D3.02 tests-first status bar");
let planned = run_stage(plan_prompt(inspect_notes, progress_notes, shell_notes), plan_opts, "D3.02 plan failed.");
let plan_notes = text_of(planned);
if planned != () && planned.success && planned.output != () {
    plan_notes = json_encode(planned.output);
}
if plan_notes == "" {
    plan_notes = "Follow D3.02 spec: tests-first statusBarModel.ts + StatusBar gated by isDesktopShell(); sidecar via GET /health; reuse processingProgress; local commit; no push.";
}

phase("Implement");
log("Implementing D3.02 status bar for sidecar and jobs");
let implemented = run_stage(implement_prompt(plan_notes), implement_opts, "D3.02 implement failed.");

phase("Verify");
log("Verifying D3.02 against spec and tests");
let verified = run_stage(verify_prompt(), verify_opts, "D3.02 verify failed.");

let files_changed = "";
let tests_run = "";
let skipped = "";
let commit = "";
let passed = false;
if implemented != () && implemented.success && implemented.output != () {
    if implemented.output.files_changed != () {
        files_changed = implemented.output.files_changed;
    }
    if implemented.output.tests_run != () {
        tests_run = implemented.output.tests_run;
    }
    if implemented.output.skipped != () {
        skipped = implemented.output.skipped;
    }
    if implemented.output.commit != () {
        commit = implemented.output.commit;
    }
}
if verified != () && verified.success && verified.output != () {
    if verified.output.files_changed != () {
        files_changed = verified.output.files_changed;
    }
    if verified.output.tests_run != () {
        tests_run = verified.output.tests_run;
    }
    if verified.output.skipped != () {
        skipped = verified.output.skipped;
    }
    if verified.output.commit != () {
        commit = verified.output.commit;
    }
    if verified.output.passed == true {
        passed = true;
    }
}

let report = "";
report += "# D3.02 Status bar\n\n";
report += "passed: " + passed.to_string() + "\n";
report += "commit: " + commit + "\n\n";
report += "## Files changed\n" + files_changed + "\n\n";
report += "## Test commands and results\n" + tests_run + "\n\n";
report += "## Skipped\n" + skipped + "\n";
let report_path = write_scratch_file("d3-02-report.md", report);

complete(#{
    summary: "D3.02 status bar workflow finished",
    passed: passed,
    commit: commit,
    files_changed: files_changed,
    tests_run: tests_run,
    skipped: skipped,
    report: report_path,
    phases: ["Investigate", "Plan", "Implement", "Verify"],
});
