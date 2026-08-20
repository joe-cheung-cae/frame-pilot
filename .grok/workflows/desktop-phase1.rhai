let meta = #{
    name: "desktop-phase1",
    description: "Serial Phase 1 desktop pipeline: 需求拆解, 评审, 归档, 开发, 测试, 上线 on feature/desktop-packaging, with a push after every stage",
    when_to_use: "Land FramePilot desktop Phase 1 (D1.01-D1.09) on feature/desktop-packaging",
    phases: [
        #{ title: "需求拆解", detail: "Break Phase 1 into an implementation contract" },
        #{ title: "评审", detail: "Review the breakdown against the live tree" },
        #{ title: "归档", detail: "Archive the accepted Phase 1 backlog" },
        #{ title: "开发", detail: "Implement D1.01-D1.09 tests-first" },
        #{ title: "测试", detail: "Run web, job, sidecar, smoke, and verify" },
        #{ title: "上线", detail: "Tick tracker, close Phase 1 handoff, push" },
    ],
};

fn stage_schema() {
    #{
        "type": "object",
        "required": ["ok", "stage", "commit", "handoff", "notes"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "stage": #{ "type": "string" },
            "commit": #{ "type": "string" },
            "handoff": #{ "type": "string" },
            "notes": #{ "type": "string" },
        },
    }
}

fn repo_path() {
    "/Users/chao/workspace/repo/frame-pilot"
}

fn scratch_path() {
    "/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-c2f1e0e66478/implementer"
}

fn shared_rules() {
    let s = "";
    s += "Repo: " + repo_path() + "\n";
    s += "Scratch (never /tmp): " + scratch_path() + "\n";
    s += "Branch must stay feature/desktop-packaging, checked out from main at 1d6ffa7. Do not checkout other branches. Do not open a PR. Do not merge to main.\n";
    s += "THIS OBJECTIVE REQUIRES git push after every finished stage. Use: git push -u origin HEAD\n";
    s += "If push fails, write the exact git error to " + scratch_path() + "/git-push.txt and still finish the product work.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, docs, commits. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not start Phase 2-5. Do not bump APP_VERSION.\n";
    s += "Do not set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME. Do not migrate apps/web off Next.js. Do not add output: export.\n";
    s += "npm run verify must not install or require rustc, cargo, or Tauri.\n";
    s += "Do not add Co-authored-by Cursor or similar trailers.\n";
    s += "Handoff contract lives in docs/handoff/STATUS.md plus the stage file named in the prompt.\n";
    s += "After the stage work, git add only relevant files, commit on feature/desktop-packaging, push, then git status and git log -1.\n";
    s += "Append git log --oneline origin/main..HEAD and git status -sb to " + scratch_path() + "/git-stage-commits.txt after every push.\n";
    s += "If nothing is staged, do not make an empty commit; write the handoff first so there is a real change.\n";
    s
}

fn medium_plan_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        reasoning_effort: "medium",
        agent_type: "plan",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn archive_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        reasoning_effort: "low",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn high_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        reasoning_effort: "high",
        agent_type: "grok-46-high",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn launch_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        reasoning_effort: "medium",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn stage_ok(r) {
    r != () && r.success
}

fn breakdown_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, plan-oriented) for stage 需求拆解.\n";
    s += shared_rules();
    s += "This stage is documentation only. Do not implement production code.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md, docs/desktop_development_plan.md Phase 1, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (D1.01-D1.09 and section 5.1), ";
    s += "docs/plans/2026-08-18-desktop-packaging-review.md, docs/desktop_goal_mode.md, ";
    s += "docs/handoff/STATUS.md, docs/desktop_feasibility_notes.md, ";
    s += "apps/web/src/lib/api.ts, apps/web/src/components/*.tsx, apps/desktop/**, package.json. ";
    s += "Confirm git branch is feature/desktop-packaging and HEAD equals origin/main at branch time except this commit.\n";
    s += "Write docs/handoff/phase1-requirements.md that decomposes desktop Phase 1 only ";
    s += "(D1.01-D1.09, not implement_goals.md Phase 1, not desktop Phases 2-5) into: ";
    s += "goal, locked decisions, in-scope ids, out-of-scope, files to create/modify, tests-first list, ";
    s += "acceptance boxes, environment notes (no rustc/cargo/rustup on this host as of 2026-08-19T08:26:40Z), and risks.\n";
    s += "Write or replace docs/handoff/STATUS.md with: current_stage=需求拆解, status=complete, ";
    s += "files changed, tests run=none (docs), next_stage=评审, blockers=none (D0.07 rustc still [~] is inherited, not a Phase 1 start blocker).\n";
    s += "If .grok/workflows/desktop-phase1.rhai exists, include it in this commit.\n";
    s += "Commit message: docs: break down desktop Phase 1 requirements\n";
    s += "Then git push -u origin HEAD.\n";
    s += "Return ok=true, stage=需求拆解, commit=full sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, plan-oriented) for stage 评审.\n";
    s += shared_rules();
    s += "Read docs/handoff/phase1-requirements.md, docs/handoff/STATUS.md, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md D1.01-D1.09, the current web/desktop files named there, ";
    s += "and AGENTS.md. Adversarially review the breakdown: missing adapter tests, Vite alias vs barrel, ";
    s += "API base resolved at call time not module freeze, isDesktopShell only literal true, ";
    s += "shared Tailwind tokens / no CSS fork, sidecar never --port 0 in shipped path, absolute --data-dir, ";
    s += "FRAMEPILOT_DESKTOP=1, ready-line parse, window injection, verify without Rust, ";
    s += "job cancel-then-restart, rustc missing so compile/WebView stay [~] unless cargo can be enabled without brew/apt.\n";
    s += "Write docs/handoff/phase1-review.md with verdict accept-with-notes, findings, and required test list ";
    s += "that matches the goal verification plan (adapters, typecheck/test:web, desktop build, verify rust-free, ";
    s += "job pytest, dual sidecar HTTP, cargo test or dated toolchain capture).\n";
    s += "Update docs/handoff/STATUS.md: current_stage=评审, next_stage=归档.\n";
    s += "Commit message: docs: review desktop Phase 1 requirements\n";
    s += "Then git push -u origin HEAD.\n";
    s += "Return ok=true, stage=评审, commit=full sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are grok-4.6 (low effort, general-purpose) for stage 归档.\n";
    s += shared_rules();
    s += "Read docs/handoff/phase1-requirements.md and docs/handoff/phase1-review.md.\n";
    s += "Write docs/handoff/phase1-backlog.md as the accepted implementation contract for D1.01-D1.09. ";
    s += "Each id: depends-on, files, implement, tests-first, commit-hint, done-when. ";
    s += "State that 开发 may make extra per-task commits but must finish with a 开发 stage commit and push.\n";
    s += "Update docs/handoff/STATUS.md: current_stage=归档, next_stage=开发.\n";
    s += "Commit message: docs: archive accepted desktop Phase 1 backlog\n";
    s += "Then git push -u origin HEAD.\n";
    s += "Return ok=true, stage=归档, commit=full sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn develop_nav_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 subtask D1.01 Navigation adapter.\n";
    s += shared_rules();
    s += "Implement D1.01 only. Tests first. Extra per-task commit is required. Do not start D1.02+.\n";
    s += "Read: docs/plans/2026-08-18-desktop-packaging.md D1.01, docs/handoff/phase1-backlog.md, ";
    s += "apps/web/src/components/Shell.tsx ProjectList.tsx ProjectDashboard.tsx ProcessingPanel.tsx ";
    s += "ImportPanel.tsx ProjectCreator.tsx CullingWorkspace.tsx and their *.test.tsx files.\n";
    s += "Create apps/web/src/lib/navigation.ts as types + re-export only from ./navigation.next.\n";
    s += "Create apps/web/src/lib/navigation.next.tsx: Link wraps next/link; useNavigator().push uses next/navigation useRouter; ";
    s += "useQueryParams() returns URLSearchParams from useSearchParams. Do not re-export next/link from a barrel used by Vite.\n";
    s += "Shared components under apps/web/src/components/ must import Link/useNavigator/useQueryParams from @/lib/navigation only. ";
    s += "No next/link or next/navigation imports under apps/web/src/components/.\n";
    s += "CullingWorkspace must use useQueryParams() not useSearchParams() directly. ProjectCreator/CullingWorkspace use useNavigator().push.\n";
    s += "Re-point mocks in CullingWorkspace.test.tsx ProcessingPanel.test.tsx ImportExportPanels.test.tsx to @/lib/navigation.\n";
    s += "Write apps/web/src/lib/navigation.test.tsx (vitest, not .test.ts): Link renders <a href>; push called with expected href; ";
    s += "useQueryParams reads a value; a guard asserts shared components do not import next/link or next/navigation.\n";
    s += "Drive the shipped adapters. Do not mock the unit under test. Do not hardcode unexpected hosts.\n";
    s += "Run npm run typecheck && npm run test:web and fix until green.\n";
    s += "Tick D1.01 [x] in docs/plans/2026-08-18-desktop-packaging.md §5.1 in the same commit.\n";
    s += "Commit message: web: isolate Next navigation behind an adapter\n";
    s += "Push. Return ok=true, stage=开发-D1.01, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn develop_api_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 subtasks D1.02 and D1.02a.\n";
    s += shared_rules();
    s += "D1.01 must already be committed. Implement D1.02 then D1.02a. Tests first for each.\n";
    s += "D1.02: Create apps/web/src/lib/apiBase.ts and apps/web/src/types/globals.d.ts. ";
    s += "resolveApiBase() order: window.__FRAMEPILOT_API_BASE__, then NEXT_PUBLIC_API_BASE_URL, then http://127.0.0.1:8000. ";
    s += "Trim trailing slashes. Missing window must not throw (safe for next build). ";
    s += "Keep exporting API_BASE but request, exportDownloadUrl, and assetUrl must call resolveApiBase() at call time. ";
    s += "Tests apps/web/src/lib/apiBase.test.ts and update apps/web/src/lib/api.test.ts: window wins; env second; default third; ";
    s += "trailing slash trimmed; no throw without window; injected base used by assetUrl and exportDownloadUrl; ";
    s += "existing assetUrl encoding assertions still hold on the default. Do not hardcode the expected host except the documented default. ";
    s += "Do not mock resolveApiBase when testing it. Do not start past resolveApiBase.\n";
    s += "Commit D1.02 as: web: resolve API base at runtime for desktop and tick D1.02 [x]. Push.\n";
    s += "D1.02a: Create apps/web/src/lib/shell.ts. isDesktopShell() true only for literal window.__FRAMEPILOT_DESKTOP__ === true. ";
    s += "False for undefined, '1', 0, or missing window. applyShellDataset() sets document.documentElement.dataset.shell to desktop or browser. ";
    s += "Call applyShellDataset from apps/web/src/components/Providers.tsx (browser -> browser). ";
    s += "Tests apps/web/src/lib/shell.test.ts. Drive the shipped isDesktopShell. Commit: web: add desktop shell detection helper and tick D1.02a [x]. Push.\n";
    s += "Run npm run typecheck && npm run test:web after each task. Update STATUS.md notes but keep current_stage conceptually 开发.\n";
    s += "Return ok=true, stage=开发-D1.02, commit=latest sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn develop_vite_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 subtasks D1.03a and D1.03b.\n";
    s += shared_rules();
    s += "D1.01/D1.02/D1.02a must already exist. Implement Vite SPA then desktop router. Tests/build first.\n";
    s += "D1.03a: Turn apps/desktop into a Vite + React SPA. Create package.json, vite.config.ts, tsconfig.json, ";
    s += "tailwind.config.ts, postcss.config.js, src/main.tsx, src/styles.css. Keep existing src-tauri tree. ";
    s += "Dependencies mirroring web: react, react-dom, tanstack query/virtual, zustand, lucide-react, plus react-router-dom. ";
    s += "Dev: vite, plugin-react, typescript, tailwindcss ^3.4, postcss, autoprefixer, @tauri-apps/cli. ";
    s += "Vite alias @ -> ../web/src. Alias navigation.next (the ./navigation.next import) to src/navigation.router.tsx. ";
    s += "server.fs.allow includes ../web. Port 1420, strictPort true. ";
    s += "Extract shared Tailwind color tokens from apps/web/tailwind.config.ts into a small shared module and import it from both configs. Do not duplicate hex. ";
    s += "src/styles.css must @import ../../web/src/app/globals.css — no CSS fork. ";
    s += "Root package.json: install:all also npm --prefix apps/desktop install; add typecheck:desktop and lint:desktop; ";
    s += "add typecheck:desktop to verify WITHOUT rustc/cargo/tauri. ";
    s += "navigation.router.tsx may be a stub until D1.03b. ";
    s += "Run npm --prefix apps/desktop install, npm --prefix apps/desktop run build (must emit non-trivial CSS), npm run typecheck:desktop. ";
    s += "Commit: desktop: add Vite build with shared aliases and Tailwind and tick D1.03a [x]. Push.\n";
    s += "D1.03b: Create apps/desktop/src/router.tsx, navigation.router.tsx (full D1.01 contract: href->to, drop prefetch), App.tsx. ";
    s += "Routes match apps/web/src/app exactly: / help settings /projects/new /projects/:projectId ";
    s += "/projects/:projectId/import process cull export. Catch-all to home. Same providers as Providers.tsx. ";
    s += "Call applyShellDataset(). Leave use client directives in shared files. ";
    s += "Replace Phase 0 placeholder index.html/health.js with the Vite entry. ";
    s += "Run typecheck:desktop, desktop build, npm run test:web. ";
    s += "Commit: desktop: add router reusing web page components and tick D1.03b [x]. Push.\n";
    s += "Return ok=true, stage=开发-D1.03, commit=latest sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn develop_sidecar_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 subtasks D1.04 D1.05 D1.06 D1.07.\n";
    s += shared_rules();
    s += "Implement sidecar lifecycle, data dir, window/single-instance, and rust-free verify scripts. Tests first for Rust helpers.\n";
    s += "You MAY try a user-space rustup install (curl https://sh.rustup.rs) if rustc is missing. NEVER brew/apt/system packages. ";
    s += "NEVER install a display server or WebView. If rustup/cargo still fail, capture exact command+error+exit to ";
    s += scratch_path() + "/tauri-toolchain.txt and keep compile/WebView ids [~]. Still land the Rust SOURCE and unit tests.\n";
    s += "D1.04: Split apps/desktop/src-tauri/src/sidecar.rs. allocate_loopback_port binds 127.0.0.1:0, reads port, drops listener. ";
    s += "Shipped spawn path ALWAYS passes --port <n>, never --port 0. Always pass absolute --data-dir. Env FRAMEPILOT_DESKTOP=1. ";
    s += "Parse stdout ready line; fail if reported port differs. Inject __FRAMEPILOT_API_BASE__ and __FRAMEPILOT_DESKTOP__=true before UI load. ";
    s += "Crash: one automatic restart; two health failures -> blocking error page. Shutdown SIGTERM, wait 5s, then kill. ";
    s += "Log sidecar stderr to {data_dir}/logs/sidecar.log. Rust unit tests for allocate_loopback_port and parse_ready_line. ";
    s += "Commit: desktop: manage sidecar lifecycle and API base injection. Tick D1.04 [x] only if cargo test ran; else [~] with dated note.\n";
    s += "D1.05: OS app-support dirs: macOS ~/Library/Application Support/FramePilot; Windows %APPDATA%\\\\FramePilot; ";
    s += "Linux ~/.local/share/FramePilot. Packaged never uses CWD-relative .framepilot-data. Dev may use .framepilot-desktop-dev. ";
    s += "Table-driven Rust tests for prefixes. Commit: desktop: use OS app-support data directory.\n";
    s += "D1.06: Title FramePilot; min size ~1100x720; remember position/size; single instance focuses first window; close stops sidecar. ";
    s += "Commit: desktop: add window state and single-instance lock. GUI [~] if no WebView/cargo.\n";
    s += "D1.07: npm run dev:desktop should run tauri dev + Vite + sidecar when cargo exists. verify must NOT require Rust. ";
    s += "install:all already installs desktop. Update apps/desktop/README.md. Commit: desktop: add tauri dev scripts and tick D1.07 [x] ";
    s += "if verify stays rust-free. Push after each task commit.\n";
    s += "Return ok=true, stage=开发-D1.04, commit=latest sha, handoff=docs/handoff/STATUS.md, notes=what landed and any [~].\n";
    s
}

fn develop_smoke_quit_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 subtasks D1.08 and D1.09 plus the 开发 stage close-out.\n";
    s += shared_rules();
    s += "D1.08: Create tests/desktop/smoke.sh (or equivalent) and npm run test:desktop:smoke. ";
    s += "Launch the REAL sidecar entry with absolute temp --data-dir and --port 0 (test path only). ";
    s += "Parse ready line host=127.0.0.1 port != 0. GET /health and GET /api/projects. ";
    s += "Health JSON has status, version, service. Projects body is a JSON array (empty OK). SIGTERM and process exits. ";
    s += "CORS/Host failure must be visible, not a silent 403. HTTP smoke is enough for the non-GUI [x]; WebView stays [~] if needed. ";
    s += "Commit: test: add desktop project-list smoke.\n";
    s += "D1.09: Reuse existing POST cancel route. Extend apps/api/tests/test_job_reliability.py on the SHIPPED cancel/retry path. ";
    s += "Do not reimplement cancel in the test. Assert: cancel-then-restart leaves no photo in processing; ";
    s += "terminal job status is cancelled not failed; a killed worker remains retryable. ";
    s += "Rust quit state machine returns Kill after the grace window (unit-testable). ";
    s += "Close-with-active-job can cancel or drain. Update docs/v2_known_limitations.md only if a remaining gap exists. ";
    s += "Commit: desktop: cancel or drain jobs before quitting.\n";
    s += "Then write/update docs/handoff/STATUS.md: current_stage=开发, status=complete, next_stage=测试, files changed, tests run. ";
    s += "Final 开发 stage commit message: desktop: complete Phase 1 development stage\n";
    s += "Push. Return ok=true only if adapters, Vite SPA, smoke script, and job tests exist. ";
    s += "stage=开发, commit=final sha, handoff=docs/handoff/STATUS.md, notes=what landed and any [~].\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for stage 测试.\n";
    s += shared_rules();
    s += "Fix until green. Drive the shipped code. No test theater.\n";
    s += "1) npm run typecheck && npm run test:web -> " + scratch_path() + "/test-web.log (exit 0)\n";
    s += "2) Run the desktop typecheck/build path; capture " + scratch_path() + "/desktop-build.log (non-trivial CSS; exit 0)\n";
    s += "3) npm run verify -> " + scratch_path() + "/verify.log (exit 0; must not install or invoke rustc/cargo/Tauri). ";
    s += "Use fail-if-invoked wrappers on PATH if needed to prove this.\n";
    s += "4) .venv/bin/pytest apps/api/tests/test_job_reliability.py -q -> " + scratch_path() + "/pytest-jobs.txt (exit 0)\n";
    s += "5) Launch the REAL sidecar entry TWICE with absolute temp --data-dir and --port 0. Parse ready line, ";
    s += "GET /health and GET /api/projects both runs, SIGTERM, process exits. ";
    s += "Capture " + scratch_path() + "/sidecar-run-1.txt and sidecar-run-2.txt. Do not invent a health/projects body if launch fails.\n";
    s += "6) If npm run test:desktop:smoke exists, run it TWICE to desktop-smoke-1.txt and desktop-smoke-2.txt.\n";
    s += "7) If cargo/rustc work, cargo test in apps/desktop/src-tauri TWICE -> cargo-test-1.txt and cargo-test-2.txt. ";
    s += "Else capture cargo --version / rustc --version exact error to " + scratch_path() + "/tauri-toolchain.txt.\n";
    s += "If anything fails, fix the shipped code and rerun. Update docs/handoff/STATUS.md current_stage=测试, next_stage=上线.\n";
    s += "Commit message: test: verify desktop Phase 1 behavior\n";
    s += "Then git push -u origin HEAD.\n";
    s += "Return ok=true only if test-web, desktop-build, verify, pytest-jobs, and both sidecar runs exited 0. ";
    s += "stage=测试, commit=sha, handoff=docs/handoff/STATUS.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, general-purpose) for stage 上线.\n";
    s += shared_rules();
    s += "上线 means close Phase 1 on feature/desktop-packaging. Do not publish installers. Do not open a PR. Do not start Phase 2.\n";
    s += "Read feasibility notes, tracker §5.1, STATUS.md, and scratch captures.\n";
    s += "Tick every Phase 1 id in section 5.1 to [x] or dated [~]. Any [~] must cite a dated command and error. ";
    s += "Tick Phase 1 acceptance boxes: home/HTTP project list, sidecar health, verify without Tauri, browser :3000/:8000.\n";
    s += "Update docs/handoff/STATUS.md current_stage=上线, status=complete, next_stage=none (Phase 2 not started).\n";
    s += "Run git log --oneline origin/main..HEAD and append to " + scratch_path() + "/git-stage-commits.txt\n";
    s += "Commit message: docs: record Phase 1 close-out and tick desktop tracker\n";
    s += "Then git push -u origin HEAD.\n";
    s += "Return ok=true, stage=上线, commit=sha, handoff=docs/handoff/STATUS.md, notes=close-out summary.\n";
    s
}

phase("需求拆解");
log("Starting 需求拆解 with medium-effort grok-4.6 plan agent");
let r1 = agent(breakdown_prompt(), medium_plan_opts("phase1-breakdown"));
if !stage_ok(r1) {
    pause("no_progress", "需求拆解 failed; inspect the agent before 评审.");
}

phase("评审");
log("Starting 评审 with medium-effort grok-4.6 plan agent");
let r2 = agent(review_prompt(), medium_plan_opts("phase1-review"));
if !stage_ok(r2) {
    pause("no_progress", "评审 failed; inspect the agent before 归档.");
}

phase("归档");
log("Starting 归档 with low-effort grok-4.6 general-purpose agent");
let r3 = agent(archive_prompt(), archive_opts("phase1-archive"));
if !stage_ok(r3) {
    pause("no_progress", "归档 failed; inspect the agent before 开发.");
}

phase("开发");
log("Starting D1.01 navigation adapter with high-effort grok-4.6");
let r4a = agent(develop_nav_prompt(), high_opts("phase1-dev-nav"));
if !stage_ok(r4a) {
    pause("no_progress", "D1.01 failed; inspect before D1.02.");
}
log("Starting D1.02/D1.02a API base and shell flag with high-effort grok-4.6");
let r4b = agent(develop_api_prompt(), high_opts("phase1-dev-api"));
if !stage_ok(r4b) {
    pause("no_progress", "D1.02 failed; inspect before D1.03.");
}
log("Starting D1.03 Vite SPA and router with high-effort grok-4.6");
let r4c = agent(develop_vite_prompt(), high_opts("phase1-dev-vite"));
if !stage_ok(r4c) {
    pause("no_progress", "D1.03 failed; inspect before sidecar work.");
}
log("Starting D1.04-D1.07 sidecar lifecycle with high-effort grok-4.6");
let r4d = agent(develop_sidecar_prompt(), high_opts("phase1-dev-sidecar"));
if !stage_ok(r4d) {
    pause("no_progress", "D1.04-D1.07 failed; inspect before smoke/quit.");
}
log("Starting D1.08-D1.09 smoke, quit, and 开发 close-out with high-effort grok-4.6");
let r4e = agent(develop_smoke_quit_prompt(), high_opts("phase1-dev-close"));
if !stage_ok(r4e) {
    pause("no_progress", "开发 close-out failed; inspect before 测试.");
}

phase("测试");
log("Starting 测试 with high-effort grok-4.6 grok-46-high agent");
let r5 = agent(test_prompt(), high_opts("phase1-test"));
if !stage_ok(r5) {
    pause("no_progress", "测试 failed; inspect the agent before 上线.");
}

phase("上线");
log("Starting 上线 with medium-effort grok-4.6 general-purpose agent");
let r6 = agent(launch_prompt(), launch_opts("phase1-launch"));
if !stage_ok(r6) {
    pause("no_progress", "上线 failed; inspect the agent.");
}

complete(#{
    summary: "Phase 1 serial pipeline finished on feature/desktop-packaging",
    stages: ["需求拆解", "评审", "归档", "开发", "测试", "上线"],
    handoff: "docs/handoff/STATUS.md",
});
