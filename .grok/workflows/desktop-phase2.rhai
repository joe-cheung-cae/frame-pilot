let meta = #{
    name: "desktop-phase2",
    description: "Serial Phase 2 desktop pipeline: 需求拆解, 评审, 归档, 开发 D2.00-D2.09 with a GitHub push after every task, 测试, 上线",
    when_to_use: "Land FramePilot desktop Phase 2 (D2.00-D2.09) on feature/desktop-phase2 and submit each task to GitHub",
    phases: [
        #{ title: "Inspect", detail: "Skip stages already committed and pushed" },
        #{ title: "需求拆解", detail: "Verify Phase 2 implementation contract" },
        #{ title: "评审", detail: "Review the breakdown against the live tree" },
        #{ title: "归档", detail: "Archive the accepted Phase 2 backlog" },
        #{ title: "开发", detail: "Implement D2.00-D2.09 tests-first, push each id" },
        #{ title: "测试", detail: "Run api, web, e2e, verify" },
        #{ title: "上线", detail: "Tick tracker, close Phase 2 against the living tracker, push, keep PR draft" },
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

fn progress_schema() {
    #{
        "type": "object",
        "required": ["notes"],
        "properties": #{
            "run_breakdown": #{ "type": "boolean" },
            "run_review": #{ "type": "boolean" },
            "run_archive": #{ "type": "boolean" },
            "run_d200": #{ "type": "boolean" },
            "run_d201": #{ "type": "boolean" },
            "run_d202": #{ "type": "boolean" },
            "run_d203": #{ "type": "boolean" },
            "run_d204": #{ "type": "boolean" },
            "run_d205": #{ "type": "boolean" },
            "run_d206": #{ "type": "boolean" },
            "run_d207": #{ "type": "boolean" },
            "run_d208": #{ "type": "boolean" },
            "run_d209": #{ "type": "boolean" },
            "run_test": #{ "type": "boolean" },
            "run_launch": #{ "type": "boolean" },
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
    s += "Fallback: GitHub MCP create_pull_request with draft true. Never open a second PR. Subsequent tasks only push; the PR updates. Existing draft PR is https://github.com/joe-cheung-cae/frame-pilot/pull/38\n";
    s += "Append SHA, subject, push result, and PR URL to $HOME/.cache/framepilot-desktop-phase2/git-github.txt after every push.\n";
    s += "If push fails, capture the exact error, retry once, then continue product work and report the blocker in session notes (do not write docs/handoff/STATUS.md); living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1.\n";
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
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>'.\n";
    s += "docs/handoff is retired. Do not create, write, or restore any docs/handoff/* file (including STATUS.md). The living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Phase 0-2 are already on main; remaining work is Phase 3-5. Do not retick completed Phase 0-2 boxes. Do not write docs/handoff/STATUS.md.\n";
    s += "After the stage work, git add only relevant files, commit on feature/desktop-phase2, push, then git status and git log -1.\n";
    s += "If nothing is staged, skip an empty commit. Do not recreate docs/handoff files.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains this stage's exact commit subject, do not redo the work. Return ok=true with that existing SHA.\n";
    s
}

fn github_tail() {
    let s = "";
    s += "Then git push -u origin HEAD.\n";
    s += "Ensure the single draft PR exists (create if missing, never a second PR). PR 38 if already open.\n";
    s += "Append SHA/subject/push/PR to $HOME/.cache/framepilot-desktop-phase2/git-github.txt.\n";
    s
}

fn agent_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn inspect_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: progress_schema(),
    }
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
    let third = agent(prompt, opts);
    if stage_ok(third) {
        return third;
    }
    await_user("no_progress", fail_msg + " Still failing. Resume to retry once more.");
    agent(prompt, opts)
}

fn progress_prompt() {
    let s = "";
    s += "Inspect FramePilot desktop Phase 2 progress. Use tools. Do not implement product code. Do not commit.\n";
    s += "Read: git rev-parse --abbrev-ref HEAD; git log origin/main..HEAD --oneline; docs/plans/2026-08-18-desktop-packaging.md; ";
    s += "docs/plans/2026-08-18-desktop-packaging.md section 5.1 Phase 2 boxes; ";
    s += "docs/handoff is retired; do not look for phase2-requirements/review/backlog. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1.\n";
    s += "Set each run_* boolean to false when that stage is already committed on feature/desktop-phase2, true when the agent must still do the work.\n";
    s += "run_breakdown false if commit subject 'docs: break down desktop Phase 2 requirements' exists.\n";
    s += "run_review false if 'docs: review desktop Phase 2 requirements' exists.\n";
    s += "run_archive false if 'docs: archive accepted desktop Phase 2 backlog' exists.\n";
    s += "run_d200 false only if §5.1 D2.00 is [x] AND commit 'api: register desktop project roots before use' exists.\n";
    s += "Same pattern for D2.01-D2.09 using their commit-hint subjects and §5.1 boxes.\n";
    s += "run_test false if 'test: verify desktop Phase 2 behavior' exists.\n";
    s += "run_launch false if 'docs: record Phase 2 close-out and tick desktop tracker' exists.\n";
    s += "If STATUS next_stage is 开发 and D2 boxes are [ ], run_d200 is true and docs run_* are false.\n";
    s += "notes: short summary of branch, PR, and next id.\n";
    s
}

fn breakdown_prompt() {
    let s = "";
    s += "You are grok-4.6 general-purpose for stage 需求拆解.\n";
    s += shared_rules();
    s += "This stage is documentation only. Do not implement production D2.00-D2.09 code.\n";
    s += "Create feature/desktop-phase2 from origin/main if it does not exist, then checkout it.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md, docs/desktop_development_plan.md Phase 2, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (D2.00-D2.09 and section 5.1), ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (2026-08-18 review findings were folded into this plan; the review file was removed), docs/desktop_goal_mode.md, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (already drafted — verify against the LIVE tree, do not invent a second architecture), ";
    s += "apps/api/app/services/projects.py, apps/web/src/lib/api.ts, apps/web/src/components/ProjectCreator.tsx, ";
    s += "ImportPanel.tsx, ExportPanel.tsx, apps/desktop/vite.config.ts, capabilities/default.json.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "branch=feature/desktop-phase2, tests_run=none (docs), blockers=none.\n";
    s += "If .grok/workflows/desktop-phase2.rhai exists, include it in this commit.\n";
    s += "Commit message: docs: break down desktop Phase 2 requirements\n";
    s += github_tail();
    s += "Return ok=true, stage=需求拆解, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are grok-4.6 general-purpose for stage 评审.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-08-18-desktop-packaging.md, docs/plans/2026-08-18-desktop-packaging.md, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md D2.00-D2.09, AGENTS.md, and the live files named in the breakdown.\n";
    s += "Adversarially review: D2.00 vs $HOME allowlist, Settings mutation, 404 when FRAMEPILOT_DESKTOP unset, ";
    s += "unchanged test_create_project_rejects_root_outside_allowlist, nativeFs Vite resolved-path alias, ";
    s += "no Tauri in Next, browser file-input invariant, remaining_paths loop of 100, drag overlay pointer-events, ";
    s += "reveal instead of download, no fs:/shell: capabilities, GitHub push-per-task + single draft PR.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Commit message: docs: review desktop Phase 2 requirements\n";
    s += github_tail();
    s += "Return ok=true, stage=评审, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are grok-4.6 general-purpose for stage 归档.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-08-18-desktop-packaging.md and docs/plans/2026-08-18-desktop-packaging.md.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Each id: depends-on, files, implement, tests-first, commit-hint, github-submit (push+draft PR), done-when.\n";
    s += "State that 开发 MUST make one product commit per id, tick that id in §5.1 in the same commit, then push.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Commit message: docs: archive accepted desktop Phase 2 backlog\n";
    s += github_tail();
    s += "Return ok=true, stage=归档, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn d2_common() {
    let s = "";
    s += "You are grok-4.6 general-purpose for one Phase 2 develop task.\n";
    s += shared_rules();
    s += "Implement ONLY the named id. Tests first. Watch the new test fail for the right reason, then implement.\n";
    s += "Read docs/plans/2026-08-18-desktop-packaging.md for that id, docs/plans/2026-08-18-desktop-packaging.md, and docs/plans/2026-08-18-desktop-packaging.md.\n";
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
    s += "POST and GET /api/desktop/project-roots only when FRAMEPILOT_DESKTOP=1, else 404. Registry is NOT inside Settings. Reuse desktop_mode_enabled().\n";
    s += "Tests apps/api/tests/test_desktop_project_roots.py plus unchanged test_create_project_rejects_root_outside_allowlist.\n";
    s += "If apps/api/tests/test_desktop_project_roots.py already exists untracked, finish it tests-first; do not discard a valid failing test.\n";
    s += "clear_registered_roots() in fixtures. Update docs/api.md.\n";
    s += "Run the named pytest until green.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.00, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
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
    s += "Shared UI must import @/lib/nativeFs only. Next must not import @tauri-apps/plugin-*. Desktop wrapper tests must not live under apps/web/src/lib/*.test.ts.\n";
    s += "Run npm run test:web and npm run typecheck:desktop.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.01, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
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
    s += "Return ok=true, stage=开发-D2.02, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
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
    s += "Return ok=true, stage=开发-D2.03, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn develop_d204_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.04 Drag and drop. Commit: desktop: add import drag-and-drop\n";
    s += "Dropped paths feed from-paths. Overlay pointer-events none unless a drag is active. Do not import on drop outside the import page.\n";
    s += "Use Tauri drag-drop if HTML5 drop has no filesystem paths. Tests: collectDroppedPaths(event). Run npm run test:web.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.04, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn develop_d205_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.05 Reveal project and export folders. Commit: desktop: reveal project and export paths in the OS file manager\n";
    s += "Open project folder and Open export folder via revealInFileManager. Folder export already returns output_path.\n";
    s += "Test: reveal callback invoked with output_path. Run npm run test:web.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.05, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn develop_d206_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.06 Recent projects. Commit: desktop: remember last opened project\n";
    s += "Last-opened project id in localStorage. GET /api/projects remains the list. No second database.\n";
    s += "Tests recentProjects.test.ts or .test.tsx. Run npm run test:web.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.06, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn develop_d207_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.07 Cross-platform path hardening. Commit: api: harden desktop import paths\n";
    s += "Windows drive letters, spaces, non-ASCII, trailing separators, reject NUL. Keep os.pathsep allowlist parsing.\n";
    s += "Skip live Win32-only cases on POSIX. Run npm run test:api.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.07, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn develop_d208_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.08 Full workflow verification. Commit: test: cover path-import process export workflow\n";
    s += "Create tests/desktop/workflow.md manual GUI checklist. Add pytest: create project, import synthetic JPEGs via from-paths, process, mark Pick, CSV/ZIP/folder export, originals unchanged.\n";
    s += "Run npm run test:api and npm run test:e2e if ImportPanel changed.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.08, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn develop_d209_prompt() {
    let s = "";
    s += d2_common();
    s += "ID: D2.09 Reveal exports instead of downloading. Commit: desktop: reveal export artifacts instead of downloading them\n";
    s += "On desktop (isDesktopShell true), replace CSV/ZIP download anchors in ExportPanel with Show in folder using output_path. No <a download>. Browser keeps current href.\n";
    s += "Tests ImportExportPanels.test.tsx both branches. Run npm run test:web.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "You may add a small 开发 close-out commit docs: record Phase 2 development stage if STATUS would otherwise be uncommitted, then push that too.\n";
    s += github_tail();
    s += "Return ok=true, stage=开发-D2.09, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary including PR URL.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are grok-4.6 general-purpose for stage 测试.\n";
    s += shared_rules();
    s += "Fix until green. Drive the shipped code. No test theater.\n";
    s += "1) npm run test:api -> $HOME/.cache/framepilot-desktop-phase2/test-api.log (exit 0)\n";
    s += "2) npm run typecheck && npm run test:web -> test-web.log (exit 0)\n";
    s += "3) npm run typecheck:desktop and npm --prefix apps/desktop run build -> desktop-build.log (exit 0)\n";
    s += "4) npm run verify -> verify.log (exit 0; must not invoke rustc/cargo/tauri). Use fail-if-invoked wrappers if needed.\n";
    s += "5) npm run test:e2e -> e2e.log (exit 0) because ImportPanel likely changed.\n";
    s += "6) Re-run the D2.08 pytest path-import process export file.\n";
    s += "7) Confirm test_create_project_rejects_root_outside_allowlist still passes unchanged.\n";
    s += "If anything fails, fix the shipped code and rerun. Do not write STATUS.md; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1.\n";
    s += "Commit message: test: verify desktop Phase 2 behavior\n";
    s += github_tail();
    s += "Return ok=true only if api, web, verify, and e2e exited 0. stage=测试, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are grok-4.6 general-purpose for stage 上线.\n";
    s += shared_rules();
    s += "上线 means close Phase 2 on feature/desktop-phase2. Do not publish installers. Do not merge to main. Do not start Phase 3.\n";
    s += "Tick every Phase 2 id in section 5.1 to [x] or dated [~]. Any [~] must cite a dated command and error (live picker clicks only).\n";
    s += "Tick Phase 2 acceptance boxes including GitHub: each D2.xx is on origin/feature/desktop-phase2; one draft PR is open.\n";
    s += "Mark the draft PR ready-for-review ONLY if tests are green; still do not merge.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Commit message: docs: record Phase 2 close-out and tick desktop tracker\n";
    s += github_tail();
    s += "Return ok=true, stage=上线, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=close-out summary with PR URL.\n";
    s
}

fn take_flag(output, value) {
    if output == () {
        true
    } else if value == () {
        true
    } else {
        value
    }
}

phase("Inspect");
log("Inspecting already-finished Phase 2 stages so this run can resume safely");
let progress = agent(progress_prompt(), inspect_opts("phase2-inspect"));
let out = ();
if progress != () && progress.success && progress.output != () {
    out = progress.output;
}
if out != () && out.notes != () {
    log(out.notes);
}
let run_breakdown = take_flag(out, if out == () { () } else { out.run_breakdown });
let run_review = take_flag(out, if out == () { () } else { out.run_review });
let run_archive = take_flag(out, if out == () { () } else { out.run_archive });
let run_d200 = take_flag(out, if out == () { () } else { out.run_d200 });
let run_d201 = take_flag(out, if out == () { () } else { out.run_d201 });
let run_d202 = take_flag(out, if out == () { () } else { out.run_d202 });
let run_d203 = take_flag(out, if out == () { () } else { out.run_d203 });
let run_d204 = take_flag(out, if out == () { () } else { out.run_d204 });
let run_d205 = take_flag(out, if out == () { () } else { out.run_d205 });
let run_d206 = take_flag(out, if out == () { () } else { out.run_d206 });
let run_d207 = take_flag(out, if out == () { () } else { out.run_d207 });
let run_d208 = take_flag(out, if out == () { () } else { out.run_d208 });
let run_d209 = take_flag(out, if out == () { () } else { out.run_d209 });
let run_test = take_flag(out, if out == () { () } else { out.run_test });
let run_launch = take_flag(out, if out == () { () } else { out.run_launch });

phase("需求拆解");
if run_breakdown {
    log("Starting 需求拆解");
    run_stage(breakdown_prompt(), agent_opts("phase2-breakdown"), "需求拆解 failed; inspect before 评审.");
} else {
    log("Skipping 需求拆解 (already committed)");
}

phase("评审");
if run_review {
    log("Starting 评审");
    run_stage(review_prompt(), agent_opts("phase2-review"), "评审 failed; inspect before 归档.");
} else {
    log("Skipping 评审 (already committed)");
}

phase("归档");
if run_archive {
    log("Starting 归档");
    run_stage(archive_prompt(), agent_opts("phase2-archive"), "归档 failed; inspect before 开发.");
} else {
    log("Skipping 归档 (already committed)");
}

phase("开发");
if run_d200 {
    log("Starting D2.00 registered project roots");
    run_stage(develop_d200_prompt(), agent_opts("phase2-d2-00"), "D2.00 failed; inspect before D2.01. Do not skip the GitHub push for a finished id.");
} else {
    log("Skipping D2.00 (already committed)");
}
if run_d201 {
    log("Starting D2.01 native file dialog adapters");
    run_stage(develop_d201_prompt(), agent_opts("phase2-d2-01"), "D2.01 failed; inspect before D2.02.");
} else {
    log("Skipping D2.01 (already committed)");
}
if run_d202 {
    log("Starting D2.02 native project create");
    run_stage(develop_d202_prompt(), agent_opts("phase2-d2-02"), "D2.02 failed; inspect before D2.03.");
} else {
    log("Skipping D2.02 (already committed)");
}
if run_d203 {
    log("Starting D2.03 path import UI");
    run_stage(develop_d203_prompt(), agent_opts("phase2-d2-03"), "D2.03 failed; inspect before D2.04.");
} else {
    log("Skipping D2.03 (already committed)");
}
if run_d204 {
    log("Starting D2.04 drag and drop");
    run_stage(develop_d204_prompt(), agent_opts("phase2-d2-04"), "D2.04 failed; inspect before D2.05.");
} else {
    log("Skipping D2.04 (already committed)");
}
if run_d205 {
    log("Starting D2.05 reveal folders");
    run_stage(develop_d205_prompt(), agent_opts("phase2-d2-05"), "D2.05 failed; inspect before D2.06.");
} else {
    log("Skipping D2.05 (already committed)");
}
if run_d206 {
    log("Starting D2.06 recent projects");
    run_stage(develop_d206_prompt(), agent_opts("phase2-d2-06"), "D2.06 failed; inspect before D2.07.");
} else {
    log("Skipping D2.06 (already committed)");
}
if run_d207 {
    log("Starting D2.07 path hardening");
    run_stage(develop_d207_prompt(), agent_opts("phase2-d2-07"), "D2.07 failed; inspect before D2.08.");
} else {
    log("Skipping D2.07 (already committed)");
}
if run_d208 {
    log("Starting D2.08 workflow verification");
    run_stage(develop_d208_prompt(), agent_opts("phase2-d2-08"), "D2.08 failed; inspect before D2.09.");
} else {
    log("Skipping D2.08 (already committed)");
}
if run_d209 {
    log("Starting D2.09 reveal exports");
    run_stage(develop_d209_prompt(), agent_opts("phase2-d2-09"), "D2.09 failed; inspect before 测试.");
} else {
    log("Skipping D2.09 (already committed)");
}

phase("测试");
if run_test {
    log("Starting 测试");
    run_stage(test_prompt(), agent_opts("phase2-test"), "测试 failed; inspect before 上线.");
} else {
    log("Skipping 测试 (already committed)");
}

phase("上线");
if run_launch {
    log("Starting 上线");
    run_stage(launch_prompt(), agent_opts("phase2-launch"), "上线 failed; inspect the agent.");
} else {
    log("Skipping 上线 (already committed)");
}

complete(#{
    summary: "Phase 2 serial pipeline finished on feature/desktop-phase2 with per-task GitHub pushes",
    stages: ["Inspect", "需求拆解", "评审", "归档", "开发", "测试", "上线"],
    handoff: "docs/plans/2026-08-18-desktop-packaging.md",
});
