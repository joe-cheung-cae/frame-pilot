let meta = #{
    name: "desktop-phase0",
    description: "Serial Phase 0 desktop pipeline: 需求拆解, 评审, 归档, 开发, 测试, 上线 on refactor",
    when_to_use: "Land FramePilot desktop Phase 0 (D0.00-D0.09) on the refactor branch",
    phases: [
        #{ title: "需求拆解", detail: "Break Phase 0 into an implementation contract" },
        #{ title: "评审", detail: "Review the breakdown against the live tree" },
        #{ title: "归档", detail: "Archive the accepted Phase 0 backlog" },
        #{ title: "开发", detail: "Implement Phase 0 APIs, packaging, and CI" },
        #{ title: "测试", detail: "Run pytest, sidecar, smoke, test:api, verify" },
        #{ title: "上线", detail: "Write go/no-go, tick tracker, close Phase 0" },
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
    "/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-a63c25686341/implementer"
}

fn shared_rules() {
    let s = "";
    s += "Repo: " + repo_path() + "\n";
    s += "Scratch (never /tmp): " + scratch_path() + "\n";
    s += "Branch must stay refactor. main is ancestor. Do not checkout other branches. Do not push. Do not open a PR.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, docs, commits. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not start Phase 1-5. Do not redo implement_goals.md Phase 0.\n";
    s += "npm run verify must not install or require Rust/Tauri.\n";
    s += "OBJECTIVE branch is refactor, not feature/desktop-packaging.\n";
    s += "docs/handoff is retired. Do not create, write, or restore any docs/handoff/* file (including STATUS.md). The living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Phase 0-2 are already on main; remaining work is Phase 3-5. Do not retick completed Phase 0-2 boxes. Do not write docs/handoff/STATUS.md.\n";
    s += "After the stage work, git add only relevant files, commit on refactor, then git status and git log -1.\n";
    s += "If nothing is staged, skip an empty commit. Do not recreate docs/handoff files.\n";
    s
}

fn medium_opts(label) {
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
    s += "Read with tools: AGENTS.md, develop_plan.md, docs/desktop_development_plan.md, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (especially D0.00-D0.09 and section 5.1), ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (2026-08-18 review findings were folded into this plan; the review file was removed), docs/desktop_goal_mode.md, ";
    s += "docs/api.md, apps/api/app/main.py, apps/api/app/api/routes.py, apps/api/app/services/importing.py, ";
    s += "apps/api/app/schemas/api.py, apps/api/tests/test_projects_api.py, package.json, ";
    s += "scripts/check-release-artifacts.sh. Confirm git branch is refactor.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "(D0.00-D0.09, not implement_goals.md Phase 0, not desktop Phases 1-5) into: ";
    s += "goal, locked decisions, in-scope ids, out-of-scope, files to create/modify, tests-first list, ";
    s += "acceptance boxes, environment notes (no rustc/cargo on this host is likely), and risks.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "files changed, tests run=none (docs), next_stage=评审, blockers=none.\n";
    s += "If .grok/workflows/desktop-phase0.rhai exists, include it in this commit.\n";
    s += "Commit message: docs: break down desktop Phase 0 requirements\n";
    s += "Return ok=true, stage=需求拆解, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, plan-oriented) for stage 评审.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-08-18-desktop-packaging.md, docs/plans/2026-08-18-desktop-packaging.md, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md D0.00-D0.09, the current API files named there, ";
    s += "and AGENTS.md. Adversarially review the breakdown: missing tests, host/origin gaps, ";
    s += "path-import chunk-of-100, original-file immutability, CI without Rust, PyInstaller one-dir, ";
    s += "Next export spike must be reverted if it breaks the web app, Tauri GUI may be blocked-gui.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "that matches the goal verification plan (sidecar args, ready-line, health version/service, ";
    s += "origin/host policy, path-import loop, source st_size/mtime/hash unchanged).\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Commit message: docs: review desktop Phase 0 requirements\n";
    s += "Return ok=true, stage=评审, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are grok-4.6 (low effort, general-purpose) for stage 归档.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-08-18-desktop-packaging.md and docs/plans/2026-08-18-desktop-packaging.md.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Each id: depends-on, files, implement, tests-first, commit-hint, done-when. ";
    s += "State that 开发 may make extra per-task commits but must finish with a 开发 stage commit.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Commit message: docs: archive accepted desktop Phase 0 backlog\n";
    s += "Return ok=true, stage=归档, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn develop_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for stage 开发.\n";
    s += shared_rules();
    s += "Implement desktop Phase 0 only (D0.00-D0.09) from docs/plans/2026-08-18-desktop-packaging.md ";
    s += "and docs/plans/2026-08-18-desktop-packaging.md. Tests first for sidecar, health, origins, path import.\n";
    s += "If .venv is missing, run npm run install:all. Do not set HOME or package-manager homes to scratch.\n";
    s += "Write failing tests, then implementation. Extra per-task commits are allowed. ";
    s += "Do not start D1/D2/D3/D4/D5. Do not bump version to 2.1.0-desktop.\n";
    s += "REQUIRED BEHAVIOR:\n";
    s += "D0.00 Create .github/workflows/verify.yml: pull_request plus push to main and feature/desktop-packaging ";
    s += "and refactor. ubuntu-latest, Python 3.11, Node 22, npm run install:all, npm run verify. ";
    s += "No Rust. No Playwright. concurrency cancel-in-progress.\n";
    s += "D0.01 Create apps/api/app/sidecar_main.py. argparse --host default 127.0.0.1, --port default 8000 ";
    s += "(0=ephemeral), --data-dir REQUIRED absolute, --log-level default info. Exit 2 if host not 127.0.0.1/localhost ";
    s += "or data-dir missing/relative. Set FRAMEPILOT_DATA_DIR before importing app.main. Bind socket, getsockname, ";
    s += "print exactly one stdout ready line flush=True: FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>. ";
    s += "Then uvicorn.Server(config).run(sockets=[sock]) with the FastAPI object, not the string app.main:app. ";
    s += "POSIX SO_REUSEADDR; do not set it on Windows. Logs to stderr only. ";
    s += "Add [project.scripts] framepilot-api = app.sidecar_main:main. ";
    s += "Tests in apps/api/tests/test_sidecar_cli.py: reject non-loopback host and relative/missing data-dir; ";
    s += "bind_listen_socket 127.0.0.1:0 non-zero port; ready_line exact; data-dir applied before settings; --help exit 0; ";
    s += "monkeypatch uvicorn.Server.run, do not start a live server in that unit file.\n";
    s += "D0.02 Create apps/api/app/core/version.py APP_VERSION = 2.0.0-rc2. Both /health and /api/health return ";
    s += "status ok, version APP_VERSION, service framepilot-api. FastAPI(version=APP_VERSION). Update docs/api.md. ";
    s += "Update test_projects_api.py to assert status/service/version==APP_VERSION, not exact equality to {status:ok} only. ";
    s += "create_app().version == APP_VERSION. No extra version literals in main.py, routes.py, or tests.\n";
    s += "D0.03 Create apps/api/app/core/origins.py. allowed_origins() always includes the four web origins on 3000/3100. ";
    s += "When FRAMEPILOT_DESKTOP=1 also add http://localhost:1420, http://127.0.0.1:1420, http://tauri.localhost, ";
    s += "https://tauri.localhost, tauri://localhost. Compute inside create_app. CORS + mutation guard share the set. ";
    s += "allow_credentials True, no wildcard. Host check on ALL methods: 403 unless hostname is 127.0.0.1, localhost, ";
    s += "::1, or tauri.localhost. Missing Host rejected. Tests apps/api/tests/test_desktop_origins.py as specified in the plan.\n";
    s += "D0.04a In importing.py add PATH_IMPORT_MAX_INPUT_ENTRIES=5000, PATH_IMPORT_MAX_EXPANDED_FILES=20000, ";
    s += "expand_import_paths(paths, project_root) -> ExpandedImportPaths(files, skipped). Rules from the plan. ";
    s += "Tests apps/api/tests/test_import_path_expansion.py.\n";
    s += "D0.04b POST /api/projects/{project_id}/imports/from-paths JSON {paths, job_id, expected_total, finalize}. ";
    s += "Expand; ValueError->422. Consume at most 100 expanded files. Return remaining_paths and expanded_total. ";
    s += "Reuse multipart job control (409 active import, stale job). Open source rb and register_import_file. ";
    s += "Do not add a second copy path. Queue derivatives on same finalize terms. ";
    s += "When finalize and a single input directory and source_root_path empty, record it as read-only metadata. ";
    s += "ImportResult gains remaining_paths default [] and expanded_total. Update docs/api.md. ";
    s += "Tests apps/api/tests/test_import_from_paths.py including a 250-file three-request client loop.\n";
    s += "D0.04c Tests apps/api/tests/test_import_from_paths_immutability.py: source st_size, st_mtime_ns, SHA-256 ";
    s += "unchanged; dir entry count unchanged; not a hard link to the copy; read-only source dir still imports; ";
    s += "cancel mid-import leaves sources untouched. Fix the service if a test fails, not the test.\n";
    s += "D0.05 packaging/pyinstaller/framepilot-api.spec one-dir named framepilot-api with the listed hiddenimports. ";
    s += "packaging/pyinstaller/build.sh. scripts/sidecar-smoke.sh: tmp absolute data-dir, --port 0, parse ready line, ";
    s += "curl /health for version, SIGTERM, exit within 5s. Prefer built binary if present else .venv python -m app.sidecar_main. ";
    s += "Root package.json scripts packaging:sidecar and test:sidecar. pip install pyinstaller in venv if needed. ";
    s += "Do not commit dist/ or build/.\n";
    s += "D0.06 Attempt Next output export in a throwaway change, record result in docs/desktop_feasibility_notes.md, ";
    s += "revert any Next config that would break the web app. Locked follow-up is Vite SPA. Do not migrate apps/web.\n";
    s += "D0.07a Exception in scripts/check-release-artifacts.sh: allowed_pattern for apps/desktop/src-tauri/icons/ ";
    s += "png|ico|icns only. Do not broaden blocked_pattern. gitignore target/ and .framepilot-desktop-dev/. ";
    s += "Update scripts/test-release-checks.sh so tracked icons pass and other png still fails.\n";
    s += "D0.07 Minimal Tauri 2 hello if possible. This host may have no rustc/cargo: run cargo --version, capture the ";
    s += "exact error, keep a skeleton if it does not break npm run verify, mark D0.07 [~] with dated command+error. ";
    s += "Do not install a system Rust toolchain unless rustup is already present and unused.\n";
    s += "D0.08/D0.09 may be drafted but 上线 owns the final go/no-go and tracker ticks.\n";
    s += "Create docs/desktop_feasibility_notes.md stub if missing (Blockers + Baselines).\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Final stage commit message: desktop: complete Phase 0 development stage\n";
    s += "Return ok=true only if sidecar/health/origins/path-import exist and new pytest files are present. ";
    s += "stage=开发, commit=final sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=what landed and any [~].\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for stage 测试.\n";
    s += shared_rules();
    s += "Fix until green. Drive the shipped code. No test theater.\n";
    s += "1) Run .venv/bin/pytest apps/api/tests/test_sidecar_cli.py apps/api/tests/test_projects_api.py ";
    s += "apps/api/tests/test_desktop_origins.py apps/api/tests/test_import_path_expansion.py ";
    s += "apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_from_paths_immutability.py -q ";
    s += "and capture " + scratch_path() + "/pytest-phase0.txt\n";
    s += "2) Launch the real sidecar entry TWICE with an absolute temp --data-dir and --port 0. ";
    s += "Parse the ready line, GET /health and once /api/health, assert JSON has status=ok plus version and service, ";
    s += "SIGTERM, process exits. Capture " + scratch_path() + "/sidecar-run-1.txt and sidecar-run-2.txt. ";
    s += "Do not invent a health body if launch fails.\n";
    s += "3) Run bash scripts/sidecar-smoke.sh if present; capture " + scratch_path() + "/sidecar-smoke.txt\n";
    s += "4) npm run test:api -> " + scratch_path() + "/test-api.log (must exit 0)\n";
    s += "5) npm run verify -> " + scratch_path() + "/verify.log (must exit 0, must not require Rust)\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "next_stage=上线, tests run with results.\n";
    s += "Commit message: test: verify desktop Phase 0 behavior\n";
    s += "Return ok=true only if pytest-phase0, both sidecar runs, test:api, and verify exited 0. ";
    s += "stage=测试, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, general-purpose) for stage 上线.\n";
    s += shared_rules();
    s += "上线 means close Phase 0 on refactor with go/no-go. Do not publish installers, push, or open a PR. Do not start Phase 1.\n";
    s += "Read feasibility notes and tracker in docs/plans/2026-08-18-desktop-packaging.md section 5.1.\n";
    s += "Write/update docs/desktop_feasibility_notes.md with measured baselines (sidecar start, health, RSS if available, ";
    s += "dist size if built, Tauri hello or blocked-gui with dated command and error) and a written go/no-go: ";
    s += "Shell stays Tauri 2 unless sidecar cannot be spawned; frontend stays Vite SPA follow-up; keep imagehash/scipy ";
    s += "unless unpacked sidecar >250 MB.\n";
    s += "Tick every Phase 0 id in section 5.1 to [x] or [~]. Any [~] must cite a dated command and error. ";
    s += "Also tick the Phase 0 acceptance boxes at the end of D0.09 if they hold.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Run git log --oneline main..refactor and write it to " + scratch_path() + "/git-stage-commits.txt\n";
    s += "Commit message: docs: record Phase 0 go-no-go and close desktop Phase 0\n";
    s += "Return ok=true, stage=上线, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=go/no-go summary.\n";
    s
}

phase("需求拆解");
log("Starting 需求拆解 with medium-effort grok-4.6 plan agent");
let r1 = agent(breakdown_prompt(), medium_opts("phase0-breakdown"));
if !stage_ok(r1) {
    pause("no_progress", "需求拆解 failed; inspect the agent before 评审.");
}

phase("评审");
log("Starting 评审 with medium-effort grok-4.6 plan agent");
let r2 = agent(review_prompt(), medium_opts("phase0-review"));
if !stage_ok(r2) {
    pause("no_progress", "评审 failed; inspect the agent before 归档.");
}

phase("归档");
log("Starting 归档 with low-effort grok-4.6 general-purpose agent");
let r3 = agent(archive_prompt(), archive_opts("phase0-archive"));
if !stage_ok(r3) {
    pause("no_progress", "归档 failed; inspect the agent before 开发.");
}

phase("开发");
log("Starting 开发 with high-effort grok-4.6 grok-46-high agent");
let r4 = agent(develop_prompt(), high_opts("phase0-develop"));
if !stage_ok(r4) {
    pause("no_progress", "开发 failed; inspect the agent before 测试.");
}

phase("测试");
log("Starting 测试 with high-effort grok-4.6 grok-46-high agent");
let r5 = agent(test_prompt(), high_opts("phase0-test"));
if !stage_ok(r5) {
    pause("no_progress", "测试 failed; inspect the agent before 上线.");
}

phase("上线");
log("Starting 上线 with medium-effort grok-4.6 general-purpose agent");
let r6 = agent(launch_prompt(), launch_opts("phase0-launch"));
if !stage_ok(r6) {
    pause("no_progress", "上线 failed; inspect the agent.");
}

complete(#{
    summary: "Phase 0 serial pipeline finished on refactor",
    stages: ["需求拆解", "评审", "归档", "开发", "测试", "上线"],
    handoff: "docs/plans/2026-08-18-desktop-packaging.md",
});
