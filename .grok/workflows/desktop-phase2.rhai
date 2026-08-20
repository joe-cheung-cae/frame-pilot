let meta = #{
    name: "desktop-phase2",
    description: "Serial Phase 2 desktop pipeline: 需求拆解, 评审, 归档, 开发 D2.00-D2.09 with a GitHub push after every task, 测试, 上线",
    when_to_use: "Land FramePilot desktop Phase 2 (D2.00-D2.09) on feature/desktop-phase2 and submit each task to GitHub",
    phases: [
        #{ title: "需求拆解", detail: "Verify Phase 2 implementation contract" },
        #{ title: "评审", detail: "Review the breakdown against the live tree" },
        #{ title: "归档", detail: "Archive the accepted Phase 2 backlog" },
        #{ title: "开发", detail: "Implement D2.00-D2.09 tests-first, push each id" },
        #{ title: "测试", detail: "Run api, web, e2e, verify" },
        #{ title: "上线", detail: "Tick tracker, close Phase 2 handoff, push, keep PR draft" },
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

fn shared_rules() {
    let s = "";
    s += "Resolve the repo with: git rev-parse --show-toplevel. Do not use /Users/chao/workspace/repo/frame-pilot.\n";
    s += "Scratch: mkdir -p \"$HOME/.cache/framepilot-desktop-phase2\" && chmod 700 that directory. Never /tmp. Never share it.\n";
    s += "Branch must stay feature/desktop-phase2, created from origin/main if missing. Do not checkout main for commits. Do not merge to main. Do not squash. Do not force-push.\n";
    s += "GITHUB RULE: after EVERY finished stage and EVERY D2.00-D2.09 task commit, run git push -u origin HEAD.\n";
    s += "After the first successful push, if no open PR exists for head feature/desktop-phase2, create ONE draft PR against main:\n";
    s += "gh pr create --repo joe-cheung-cae/frame-pilot --base main --head feature/desktop-phase2 --draft --title \"desktop: Phase 2 native filesystem and core workflow\" --body \"Phase 2 D2.00-D2.09. APP_VERSION stays 2.0.0-rc2. Do not merge from this body.\"\n";
    s += "Fallback: GitHub MCP create_pull_request with draft true. Never open a second PR. Subsequent tasks only push; the PR updates.\n";
    s += "Append SHA, subject, push result, and PR URL to $HOME/.cache/framepilot-desktop-phase2/git-github.txt after every push.\n";
    s += "If push fails, capture the exact error, retry once, then continue product work and report the blocker in docs/handoff/STATUS.md.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, docs, commits. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not start Phase 3-5. Do not bump APP_VERSION.\n";
    s += "Do not set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME, /, or a drive root.\n";
    s += "Do not migrate apps/web off Next.js. Do not add output: export.\n";
    s += "Do not remove the two ImportPanel file inputs when isDesktopShell is false.\n";
    s += "Do not weaken test_create_project_rejects_root_outside_allowlist.\n";
    s += "npm run verify must not install or require rustc, cargo, or Tauri.\n";
    s += "Do not add Co-authored-by Cursor or similar trailers.\n";
    s += "Handoff contract lives in docs/handoff/STATUS.md plus the stage file named in the prompt.\n";
    s += "After the stage work, git add only relevant files, commit on feature/desktop-phase2, push, then git status and git log -1.\n";
    s += "If nothing is staged, do not make an empty commit; write the handoff first so there is a real change.\n";
    s
}

fn github_tail() {
    let s = "";
    s += "Then git push -u origin HEAD.\n";
    s += "Ensure the single draft PR exists (create if missing, never a second PR).\n";
    s += "Append SHA/subject/push/PR to $HOME/.cache/framepilot-desktop-phase2/git-github.txt.\n";
    s
}

fn medium_plan_opts(label) {
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
        agent_type: "general-purpose",
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
    s += "This stage is documentation only. Do not implement production D2.00-D2.09 code.\n";
    s += "Create feature/desktop-phase2 from origin/main if it does not exist, then checkout it.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md, docs/desktop_development_plan.md Phase 2, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (D2.00-D2.09 and section 5.1), ";
    s += "docs/plans/2026-08-18-desktop-packaging-review.md A2.3, docs/desktop_goal_mode.md, ";
    s += "docs/handoff/phase2-requirements.md (already drafted — verify against the LIVE tree, do not invent a second architecture), ";
    s += "apps/api/app/services/projects.py, apps/web/src/lib/api.ts, apps/web/src/components/ProjectCreator.tsx, ";
    s += "ImportPanel.tsx, ExportPanel.tsx, apps/desktop/vite.config.ts, capabilities/default.json.\n";
    s += "Update docs/handoff/phase2-requirements.md only if live-tree facts drifted. Keep GitHub protocol section 7.\n";
    s += "Write or replace docs/handoff/STATUS.md: current_stage=需求拆解, status=complete, next_stage=评审, ";
    s += "branch=feature/desktop-phase2, tests_run=none (docs), blockers=none.\n";
    s += "If .grok/workflows/desktop-phase2.rhai exists, include it in this commit.\n";
    s += "Commit message: docs: break down desktop Phase 2 requirements\n";
    s += github_tail();
    s += "Return ok=true, stage=需求拆解, commit=full sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, plan-oriented) for stage 评审.\n";
    s += shared_rules();
    s += "Read docs/handoff/phase2-requirements.md, docs/handoff/STATUS.md, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md D2.00-D2.09, AGENTS.md, and the live files named in the breakdown.\n";
    s += "Adversarially review: D2.00 vs $HOME allowlist, Settings mutation, 404 when FRAMEPILOT_DESKTOP unset, ";
    s += "unchanged test_create_project_rejects_root_outside_allowlist, nativeFs Vite resolved-path alias, ";
    s += "no Tauri in Next, browser file-input invariant, remaining_paths loop of 100, drag overlay pointer-events, ";
    s += "reveal instead of download, no fs:/shell: capabilities, GitHub push-per-task + single draft PR.\n";
    s += "Write docs/handoff/phase2-review.md with verdict accept-with-notes, findings, and required test list.\n";
    s += "Update docs/handoff/STATUS.md: current_stage=评审, next_stage=归档.\n";
    s += "Commit message: docs: review desktop Phase 2 requirements\n";
    s += github_tail();
    s += "Return ok=true, stage=评审, commit=full sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are grok-4.6 (low effort, general-purpose) for stage 归档.\n";
    s += shared_rules();
    s += "Read docs/handoff/phase2-requirements.md and docs/handoff/phase2-review.md.\n";
    s += "Write docs/handoff/phase2-backlog.md as the accepted implementation contract for D2.00-D2.09. ";
    s += "Each id: depends-on, files, implement, tests-first, commit-hint, github-submit (push+draft PR), done-when.\n";
    s += "State that 开发 MUST make one product commit per id, tick that id in §5.1 in the same commit, then push.\n";
    s += "Update docs/handoff/STATUS.md: current_stage=归档, next_stage=开发.\n";
    s += "Commit message: docs: archive accepted desktop Phase 2 backlog\n";
    s += github_tail();
    s += "Return ok=true, stage=归档, commit=full sha, handoff=docs/handoff/STATUS.md, notes=summary.\n";
    s
}

fn d2_common() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for one Phase 2 develop task.\n";
    s += shared_rules();
    s += "Implement ONLY the named id. Tests first. Watch the new test fail for the right reason, then implement.\n";
    s += "Read docs/plans/2026-08-18-desktop-packaging.md for that id, docs/handoff/phase2-backlog.md, and docs/handoff/phase2-requirements.md.\n";
    s += "Tick exactly that id to [x] in docs/plans/2026-08-18-desktop-packaging.md §5.1 in the SAME commit. Do not tick other ids.\n";
    s += "Do not start the next D2 id. Drive shipped code. Do not mock the unit under test.\n";
    s
}

fn develop_d200_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.00 Registered project roots. Commit: api: register desktop project roots before use\n";
    s += "Create apps/api/app/core/project_roots.py. Persist {data_dir}/desktop_project_roots.json, cap 50.\n";
    s += "register_root: absolute, exists, directory, resolved. Reject BLOCKED_ROOT_NAMES, anchors, data dir and its parents.\n";
    s += "create_project allowed roots = [projects_root, *allowlist, *registered_roots()]. Do not change error message strings.\n";
    s += "POST and GET /api/desktop/project-roots only when FRAMEPILOT_DESKTOP=1, else 404. Registry is NOT inside Settings.\n";
    s += "Tests apps/api/tests/test_desktop_project_roots.py plus unchanged test_create_project_rejects_root_outside_allowlist.\n";
    s += "clear_registered_roots() in fixtures. Update docs/api.md.\n";
    s += "Run the named pytest until green.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.00, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d201_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.01 Native file dialog adapters. Commit: desktop: add native file dialog adapters\n";
    s += "Create apps/web/src/lib/nativeFs.ts: getNativeFs() returns null. Tests nativeFs.test.ts cover null without window and in browser.\n";
    s += "Create apps/desktop/src/lib/nativeFs.ts: pickDirectory, pickImageFiles, revealInFileManager via Tauri dialog + opener plugins.\n";
    s += "Vite alias the RESOLVED path of apps/web/src/lib/nativeFs.ts to apps/desktop/src/lib/nativeFs.ts (copy navigation.next plugin style).\n";
    s += "Add plugins to Cargo.toml, capabilities (dialog + opener only; NO fs: and NO shell:), and lib.rs init.\n";
    s += "Shared UI must import @/lib/nativeFs only. Next must not import @tauri-apps/plugin-*.\n";
    s += "Run npm run test:web and npm run typecheck:desktop.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.01, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d202_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.02 Project create with native picker. Commit: web: use native directory picker when desktop APIs exist\n";
    s += "D2.00 and D2.01 must already be committed and pushed.\n";
    s += "Extend api.createProject with optional acknowledgeNonempty. ProjectCreator: if getNativeFs(), Browse registers then fills root_path.\n";
    s += "Confirm copy exactly: This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?\n";
    s += "acknowledgeNonempty only after confirmation. Browser text field stays. Surface 422 verbatim.\n";
    s += "Tests: projectCreation.test.ts; API registered nonempty root fails without flag and succeeds with it; existing files remain.\n";
    s += "Run npm run test:web and the API tests.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.02, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d203_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.03 Import panel path import. Commit: web: import from local paths in desktop mode\n";
    s += "Add api.importPhotosFromPaths that loops remaining_paths with the same job_id; finalize true only on the last slice. Progress uses expanded_total.\n";
    s += "Desktop ImportPanel: pick folder/files then from-paths. Browser: existing multipart.\n";
    s += "INVARIANT: when isDesktopShell() is false, both file inputs (including webkitdirectory) keep current DOM position, labels, and disabled semantics.\n";
    s += "Tests: importWorkflow.test.ts remaining-paths loop. Run npm run test:web.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.03, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d204_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.04 Drag and drop. Commit: desktop: add import drag-and-drop\n";
    s += "Dropped paths feed from-paths. Overlay pointer-events none unless a drag is active. Do not import on drop outside the import page.\n";
    s += "Use Tauri drag-drop if HTML5 drop has no filesystem paths. Tests: collectDroppedPaths(event). Run npm run test:web.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.04, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d205_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.05 Reveal project and export folders. Commit: desktop: reveal project and export paths in the OS file manager\n";
    s += "Open project folder and Open export folder via revealInFileManager. Folder export already returns output_path.\n";
    s += "Test: reveal callback invoked with output_path. Run npm run test:web.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.05, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d206_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.06 Recent projects. Commit: desktop: remember last opened project\n";
    s += "Last-opened project id in localStorage. GET /api/projects remains the list. No second database.\n";
    s += "Tests recentProjects.test.ts or .test.tsx. Run npm run test:web.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.06, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d207_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.07 Cross-platform path hardening. Commit: api: harden desktop import paths\n";
    s += "Windows drive letters, spaces, non-ASCII, trailing separators, reject NUL. Keep os.pathsep allowlist parsing.\n";
    s += "Skip live Win32-only cases on POSIX. Run npm run test:api.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.07, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d208_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.08 Full workflow verification. Commit: test: cover path-import process export workflow\n";
    s += "Create tests/desktop/workflow.md manual GUI checklist. Add pytest: create project, import synthetic JPEGs via from-paths, process, mark Pick, CSV/ZIP/folder export, originals unchanged.\n";
    s += "Run npm run test:api and npm run test:e2e if ImportPanel changed.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.08, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn develop_d209_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.09 Reveal exports instead of downloading. Commit: desktop: reveal export artifacts instead of downloading them\n";
    s += "On desktop (isDesktopShell true), replace CSV/ZIP download anchors in ExportPanel with Show in folder using output_path. No <a download>. Browser keeps current href.\n";
    s += "Tests ImportExportPanels.test.tsx both branches. Run npm run test:web.\n";
    s += "Then write/update docs/handoff/STATUS.md current_stage=开发, status=complete, next_stage=测试.\n";
    s += "You may add a small 开发 close-out commit docs: record Phase 2 development stage if STATUS would otherwise be uncommitted, then push that too.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.09, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary including PR URL.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for stage 测试.\n";
    s += shared_rules();
    s += "Fix until green. Drive the shipped code. No test theater.\n";
    s += "1) npm run test:api -> $HOME/.cache/framepilot-desktop-phase2/test-api.log (exit 0)\n";
    s += "2) npm run typecheck && npm run test:web -> test-web.log (exit 0)\n";
    s += "3) npm run typecheck:desktop and npm --prefix apps/desktop run build -> desktop-build.log (exit 0)\n";
    s += "4) npm run verify -> verify.log (exit 0; must not invoke rustc/cargo/tauri). Use fail-if-invoked wrappers if needed.\n";
    s += "5) npm run test:e2e -> e2e.log (exit 0) because ImportPanel likely changed.\n";
    s += "6) Re-run the D2.08 pytest path-import process export file.\n";
    s += "7) Confirm test_create_project_rejects_root_outside_allowlist still passes unchanged.\n";
    s += "If anything fails, fix the shipped code and rerun. Update STATUS.md current_stage=测试, next_stage=上线.\n";
    s += "Commit message: test: verify desktop Phase 2 behavior\n";
    s += github_tail();
    s += "Return ok=true only if api, web, verify, and e2e exited 0. stage=测试, commit=sha, handoff=docs/handoff/STATUS.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, general-purpose) for stage 上线.\n";
    s += shared_rules();
    s += "上线 means close Phase 2 on feature/desktop-phase2. Do not publish installers. Do not merge to main. Do not start Phase 3.\n";
    s += "Tick every Phase 2 id in section 5.1 to [x] or dated [~]. Any [~] must cite a dated command and error (live picker clicks only).\n";
    s += "Tick Phase 2 acceptance boxes including GitHub: each D2.xx is on origin/feature/desktop-phase2; one draft PR is open.\n";
    s += "Mark the draft PR ready-for-review ONLY if tests are green; still do not merge.\n";
    s += "Update docs/handoff/STATUS.md current_stage=上线, status=complete, next_stage=none (Phase 3 not started).\n";
    s += "Commit message: docs: record Phase 2 close-out and tick desktop tracker\n";
    s += github_tail();
    s += "Return ok=true, stage=上线, commit=sha, handoff=docs/handoff/STATUS.md, notes=close-out summary with PR URL.\n";
    s
}

phase("需求拆解");
log("Starting 需求拆解 with medium-effort grok-4.6 plan agent");
let r1 = agent(breakdown_prompt(), medium_plan_opts("phase2-breakdown"));
if !stage_ok(r1) {
    pause("no_progress", "需求拆解 failed; inspect the agent before 评审.");
}

phase("评审");
log("Starting 评审 with medium-effort grok-4.6 plan agent");
let r2 = agent(review_prompt(), medium_plan_opts("phase2-review"));
if !stage_ok(r2) {
    pause("no_progress", "评审 failed; inspect the agent before 归档.");
}

phase("归档");
log("Starting 归档 with low-effort grok-4.6 general-purpose agent");
let r3 = agent(archive_prompt(), archive_opts("phase2-archive"));
if !stage_ok(r3) {
    pause("no_progress", "归档 failed; inspect the agent before 开发.");
}

phase("开发");
log("Starting D2.00 registered project roots");
let d00 = agent(develop_d200_prompt(), high_opts("phase2-d2-00"));
if !stage_ok(d00) {
    pause("no_progress", "D2.00 failed; inspect before D2.01. Do not skip the GitHub push for a finished id.");
}
log("Starting D2.01 native file dialog adapters");
let d01 = agent(develop_d201_prompt(), high_opts("phase2-d2-01"));
if !stage_ok(d01) {
    pause("no_progress", "D2.01 failed; inspect before D2.02.");
}
log("Starting D2.02 native project create");
let d02 = agent(develop_d202_prompt(), high_opts("phase2-d2-02"));
if !stage_ok(d02) {
    pause("no_progress", "D2.02 failed; inspect before D2.03.");
}
log("Starting D2.03 path import UI");
let d03 = agent(develop_d203_prompt(), high_opts("phase2-d2-03"));
if !stage_ok(d03) {
    pause("no_progress", "D2.03 failed; inspect before D2.04.");
}
log("Starting D2.04 drag and drop");
let d04 = agent(develop_d204_prompt(), high_opts("phase2-d2-04"));
if !stage_ok(d04) {
    pause("no_progress", "D2.04 failed; inspect before D2.05.");
}
log("Starting D2.05 reveal folders");
let d05 = agent(develop_d205_prompt(), high_opts("phase2-d2-05"));
if !stage_ok(d05) {
    pause("no_progress", "D2.05 failed; inspect before D2.06.");
}
log("Starting D2.06 recent projects");
let d06 = agent(develop_d206_prompt(), high_opts("phase2-d2-06"));
if !stage_ok(d06) {
    pause("no_progress", "D2.06 failed; inspect before D2.07.");
}
log("Starting D2.07 path hardening");
let d07 = agent(develop_d207_prompt(), high_opts("phase2-d2-07"));
if !stage_ok(d07) {
    pause("no_progress", "D2.07 failed; inspect before D2.08.");
}
log("Starting D2.08 workflow verification");
let d08 = agent(develop_d208_prompt(), high_opts("phase2-d2-08"));
if !stage_ok(d08) {
    pause("no_progress", "D2.08 failed; inspect before D2.09.");
}
log("Starting D2.09 reveal exports");
let d09 = agent(develop_d209_prompt(), high_opts("phase2-d2-09"));
if !stage_ok(d09) {
    pause("no_progress", "D2.09 failed; inspect before 测试.");
}

phase("测试");
log("Starting 测试 with high-effort grok-4.6");
let r5 = agent(test_prompt(), high_opts("phase2-test"));
if !stage_ok(r5) {
    pause("no_progress", "测试 failed; inspect the agent before 上线.");
}

phase("上线");
log("Starting 上线 with medium-effort grok-4.6 general-purpose agent");
let r6 = agent(launch_prompt(), launch_opts("phase2-launch"));
if !stage_ok(r6) {
    pause("no_progress", "上线 failed; inspect the agent.");
}

complete(#{
    summary: "Phase 2 serial pipeline finished on feature/desktop-phase2 with per-task GitHub pushes",
    stages: ["需求拆解", "评审", "归档", "开发", "测试", "上线"],
    handoff: "docs/handoff/STATUS.md",
});
