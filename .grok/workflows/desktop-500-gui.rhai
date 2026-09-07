let meta = #{
    name: "desktop-500-gui",
    description: "Serial leftover pipeline: 需求拆解, 评审, 归档, 开发, 测试, 上线 for unattended packaged-desktop ≥500 GUI",
    when_to_use: "Land leftover unattended packaged-desktop ≥500 GUI on feature/desktop-500-gui without inventing Phase 10",
    phases: [
        #{ title: "Inspect", detail: "Skip stages already committed and pushed" },
        #{ title: "需求拆解", detail: "Already landed Slice 0; skip unless missing" },
        #{ title: "评审", detail: "Adversarial review against live leftover plan and tree" },
        #{ title: "归档", detail: "Confirm leftover board is ready for 开发" },
        #{ title: "开发", detail: "Slice 2 harness, Slice 3 QA gate, Slice 4 desktop.yml" },
        #{ title: "测试", detail: "Linux skip-not-pass, python discovery, npm run verify" },
        #{ title: "上线", detail: "desktop.yml oracle; tick §2.2 only if both OS 500 pass" },
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
            "run_dev2": #{ "type": "boolean" },
            "run_dev3": #{ "type": "boolean" },
            "run_dev4": #{ "type": "boolean" },
            "run_test": #{ "type": "boolean" },
            "run_launch": #{ "type": "boolean" },
            "issue": #{ "type": "string" },
            "notes": #{ "type": "string" },
        },
    }
}

fn test_schema() {
    #{
        "type": "object",
        "required": ["ok", "stage", "commit", "handoff", "notes", "passed"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "passed": #{ "type": "boolean" },
            "stage": #{ "type": "string" },
            "commit": #{ "type": "string" },
            "handoff": #{ "type": "string" },
            "notes": #{ "type": "string" },
        },
    }
}

fn skeptic_schema() {
    #{
        "type": "object",
        "required": ["ok", "real", "evidence", "notes"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "real": #{ "type": "boolean" },
            "evidence": #{ "type": "string" },
            "notes": #{ "type": "string" },
        },
    }
}

fn repo_root() {
    "/home/joe/repo/frame-pilot-desktop-500-gui"
}

fn subject_schedule() {
    "docs: leftover plan for unattended packaged-desktop ≥500 GUI"
}

fn subject_review() {
    "docs: review leftover unattended packaged-desktop ≥500 GUI"
}

fn subject_archive() {
    "docs: archive leftover unattended packaged-desktop ≥500 GUI"
}

fn subject_dev2() {
    "ci: add packaged desktop ≥500 GUI harness script"
}

fn subject_dev3() {
    "feat(desktop): gated QA path injection for unattended from-paths"
}

fn subject_dev4() {
    "ci: run packaged ≥500 GUI probe and 500 after NSIS/DMG upload"
}

fn subject_evidence() {
    "docs: record packaged-desktop ≥500 GUI unattended pass"
}

fn repo_rules() {
    let s = "";
    s += "REPO ROOT is exactly /home/joe/repo/frame-pilot-desktop-500-gui (git worktree on feature/desktop-500-gui). ";
    s += "All git, npm, file edits, and tests MUST use that directory. Never commit on feature/macos-gui-dod. Never edit /home/joe/repo/frame-pilot except if it is this worktree.\n";
    s += "ONE TASK ONLY: leftover unattended packaged-desktop ≥500 GUI. GitHub issue joe-cheung-cae/frame-pilot#179. Draft PR #180. Do not invent Phase 10 / S10 / 2.3.\n";
    s += "Read docs/plans/2026-09-07-desktop-500-gui.md and the zh counterpart before writing. Discover the issue number from that plan; never guess.\n";
    s += "Branch must stay feature/desktop-500-gui. Do not checkout main for commits. Do not merge to main. Do not squash. Do not force-push. Never a second PR.\n";
    s += "isolation_worktree is false. Edit the named worktree. Do not create another worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, commits. Bilingual living docs when you touch docs. Local-first. Never modify or delete original photos. Do not commit camera photos, certs, or model weights. Never attach photos/DBs/export trees to GitHub artifacts.\n";
    s += "Path B only (QA injection inside packaged WebView). Native dialog stubbed. Do not ship Path C WebDriver. Path D perf:api is not DoD. Do not tick §2.2 with Playwright test:e2e:real-browser:large or perf:api 500.\n";
    s += "Linux/WSL2: skip is not pass, exit 2, never print result=pass. GHA windows-latest/macos-latest: fail (exit 1), never skip.\n";
    s += "Do not launch packaged GUI from verify.yml. Do not edit verify.yml. npm run verify must stay rust-free. Do not bump APP_VERSION. Product stays 2.1.0-desktop. Do not sign. Do not fold 500-import into macos-dmg-gui-smoke.sh.\n";
    s += "Scratch prefix: $HOME/.cache/framepilot-desktop-500-gui or %LOCALAPPDATA%\\framepilot-desktop-500-gui. Never /tmp for QA photos.\n";
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>'.\n";
    s += "Do not add Co-authored-by Cursor or similar trailers.\n";
    s += "YOU ARE NOT READ-ONLY. capability_mode all. You have run_terminal_command, git, gh, search_replace, write, and GitHub MCP (search_tool then github__issue_write / add_issue_comment). Do not return ok=false claiming plan mode or missing tools.\n";
    s += "GITHUB: after every finished stage commit, git push -u origin HEAD from the worktree. Single draft PR #180 already exists (Refs #179 only). Never open a second PR. Do not say Fixes until 上线 when BOTH OS 500 are result=pass.\n";
    s += "Append SHA, subject, push result, and PR URL to $HOME/.cache/framepilot-desktop-500-gui/git-github.txt after every push.\n";
    s
}

fn github_tail() {
    let s = "";
    s += "Then git -C /home/joe/repo/frame-pilot-desktop-500-gui push -u origin HEAD.\n";
    s += "Do not create a second PR. Draft PR is #180.\n";
    s += "mkdir -p $HOME/.cache/framepilot-desktop-500-gui && chmod 700 it. Append SHA/subject/push/PR to $HOME/.cache/framepilot-desktop-500-gui/git-github.txt.\n";
    s
}

fn agent_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn inspect_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: progress_schema(),
    }
}

fn test_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: test_schema(),
    }
}

fn skeptic_opts(label) {
    #{
        label: label,
        capability_mode: "read-only",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: skeptic_schema(),
    }
}

fn stage_ok(r) {
    r != () && r.success
}

fn declared_ok(r) {
    if r == () || r.output == () {
        return true;
    }
    if r.output.ok == () {
        return true;
    }
    r.output.ok == true
}

fn declared_passed(r) {
    if r == () || r.output == () {
        return true;
    }
    if r.output.passed == () {
        return true;
    }
    r.output.passed == true
}

fn should_run(v) {
    if v == () {
        return true;
    }
    v == true
}

fn run_stage(prompt, opts, fail_msg) {
    let first = agent(prompt, opts);
    if stage_ok(first) && declared_ok(first) {
        return first;
    }
    log("Retrying once: " + fail_msg);
    let second = agent(prompt, opts);
    if stage_ok(second) && declared_ok(second) {
        return second;
    }
    await_user("verification", fail_msg + " Resume to retry this stage. Do not skip ahead.");
    let third = agent(prompt, opts);
    if stage_ok(third) && declared_ok(third) {
        return third;
    }
    await_user("no_progress", fail_msg + " Still failing. Resume to retry once more.");
    agent(prompt, opts)
}

fn inspect_prompt() {
    let s = "";
    s += "Inspect FramePilot leftover unattended packaged-desktop ≥500 GUI progress. Use tools. Do not implement product code. Do not commit.\n";
    s += "Work only in /home/joe/repo/frame-pilot-desktop-500-gui. Run: git -C that path rev-parse --abbrev-ref HEAD; git log origin/main..HEAD --format='%s'; uname -s.\n";
    s += "Read docs/plans/2026-09-07-desktop-500-gui.md status board; docs/desktop_development_plan.md section 2.2 ≥500 row; .github/workflows/desktop.yml after Upload macOS DMG.\n";
    s += "Search git log origin/main..HEAD subjects and set run_* false when that commit already exists, true when the agent must still do the work:\n";
    s += "run_breakdown false if subject 'docs: leftover plan for unattended packaged-desktop ≥500 GUI' exists.\n";
    s += "run_review false if subject 'docs: review leftover unattended packaged-desktop ≥500 GUI' exists.\n";
    s += "run_archive false if subject 'docs: archive leftover unattended packaged-desktop ≥500 GUI' exists.\n";
    s += "run_dev2 false if subject 'ci: add packaged desktop ≥500 GUI harness script' exists.\n";
    s += "run_dev3 false if subject 'feat(desktop): gated QA path injection for unattended from-paths' exists.\n";
    s += "run_dev4 false if subject 'ci: run packaged ≥500 GUI probe and 500 after NSIS/DMG upload' exists.\n";
    s += "run_test true unless all of run_dev2/3/4 are false AND you have evidence npm run verify was green for HEAD; when unsure set true.\n";
    s += "run_launch false if subject 'docs: record packaged-desktop ≥500 GUI unattended pass' exists.\n";
    s += "issue: '179' if the plan cites joe-cheung-cae/frame-pilot#179, else empty. Do not guess.\n";
    s += "notes: branch, uname, Slice 1 present?, desktop.yml still without NSIS 500 step?, next stage.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are the 评审 agent for leftover unattended packaged-desktop ≥500 GUI (#179). Adversarially review the leftover plan against the live tree in /home/joe/repo/frame-pilot-desktop-500-gui. Do not implement harness launch or desktop.yml probe steps yet.\n";
    s += repo_rules();
    s += "Read docs/plans/2026-09-07-desktop-500-gui.md (+ zh), develop_plan.md 1.1, docs/desktop_development_plan.md 2.2, .github/workflows/desktop.yml, .github/workflows/verify.yml, packaging/scripts/desktop-500-gui.sh, tests/desktop/desktop-500-gui-linux.sh, scripts/test-release-checks.sh NSIS GUI assertion.\n";
    s += "Confirm: Path B lock; both-OS tick lock; skip≠pass exit 2; Slice 1 Linux check exists; #177 smoke exists on this baseline and 500 must not fold into macos-dmg-gui-smoke.sh; verify.yml rust-free; §2.2 ≥500 still [ ]; issue #179; PR #180 Refs only; no Phase 10.\n";
    s += "Fix bilingual plan holes only if the live tree makes the spec wrong. Tick leftover-plan 评审 [x] in this commit. Leave 开发 [ ]. Do not tick §2.2.\n";
    s += "If .grok/workflows/desktop-500-gui.rhai exists in the worktree, include it in this commit if untracked.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: review leftover unattended packaged-desktop ≥500 GUI', do not redo. Return ok=true with that SHA.\n";
    s += "Commit subject exactly: docs: review leftover unattended packaged-desktop ≥500 GUI\n";
    s += "If nothing is staged, skip an empty commit and still return ok=true.\n";
    s += github_tail();
    s += "Return ok=true, stage=评审, commit=HEAD sha, handoff=docs/plans/2026-09-07-desktop-500-gui.md, notes=review summary.\n";
    s
}

fn skeptic_prompt() {
    let s = "";
    s += "You are a read-only skeptic for leftover #179 packaged-desktop ≥500 GUI. Use grep/read_file/git in /home/joe/repo/frame-pilot-desktop-500-gui. Do not edit.\n";
    s += "Confirm with evidence (file:line) ALL of: (1) docs/desktop_development_plan.md §2.2 ≥500 row is still [ ]; (2) tests/desktop/desktop-500-gui-linux.sh exists and requires exit 2 + skip is not pass; (3) desktop.yml currently does not launch packaged NSIS GUI (test-release-checks assertion still present); (4) verify.yml does not launch packaged GUI; (5) uname on this host is not Darwin/Windows packaged GUI, so local 500 pass is impossible; (6) leftover plan forbids Playwright/perf:api as DoD; (7) originals are not modified by this leftover; (8) work is on feature/desktop-500-gui not macos-gui-dod.\n";
    s += "Set real=true only with evidence you independently read. Set ok=true if this leftover is still the right next slice. notes=short. evidence=file:line citations.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are the 归档 agent for leftover #179. Do not implement harness launch or desktop.yml yet. Work in /home/joe/repo/frame-pilot-desktop-500-gui.\n";
    s += repo_rules();
    s += "Read leftover plan status board. 开发 must still be [ ] unless develop subjects already exist.\n";
    s += "Record that 开发 MUST land Slice 2 harness+python, Slice 3 QA gate, Slice 4 desktop.yml+awk together; tick leftover-plan 开发 [x] only after Slice 4; must NOT tick §2.2 until both OS 500 pass.\n";
    s += "Tick leftover-plan 归档 [x] (en+zh) in this commit. Leave 开发 [ ].\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: archive leftover unattended packaged-desktop ≥500 GUI', do not redo. Return ok=true with that SHA.\n";
    s += "Commit subject exactly: docs: archive leftover unattended packaged-desktop ≥500 GUI\n";
    s += "If nothing is staged, skip an empty commit and return ok=true.\n";
    s += github_tail();
    s += "Return ok=true, stage=归档, commit=HEAD sha, handoff=docs/plans/2026-09-07-desktop-500-gui.md, notes=ready for 开发.\n";
    s
}

fn develop2_prompt() {
    let s = "";
    s += "You are the 开发 Slice 2 agent for leftover #179. Harness + Python discovery. No production Rust/SPA QA gate yet. No desktop.yml probe steps yet. Work in /home/joe/repo/frame-pilot-desktop-500-gui.\n";
    s += repo_rules();
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'ci: add packaged desktop ≥500 GUI harness script', do not redo. Return ok=true with that SHA.\n";
    s += "Read leftover plan sections 6, 8, 10, 12 Slice 2. Expand packaging/scripts/desktop-500-gui.sh (replace Slice 1 stub but KEEP Linux skip-not-pass exit 2 before generating photos). Implement: --probe and --count N; Windows-safe Python resolver (PYTHON, then .venv/Scripts/python.exe, then .venv/bin/python; never npm generate:synthetic; never PYTHONPATH); --resolve-python that prints the chosen path and exits 0; dataset generate via python -m app.devtools.synthetic_dataset --width 3000 --height 2000 --quality 88; scratch siblings photos/project/data/evidence under hard-coded prefix; start-of-run wipe; EXIT trap copies result.json to ${RUNNER_TEMP:-/tmp}/desktop-500-gui/{mode}-{os}/ THEN wipes photos/project/data/evidence; RSS sampling stubs OK on Linux because we skip before launch; always write result.json with result=skip on Linux.\n";
    s += "On Linux: after uname check, print skip is not pass, write result.json result=skip if possible, exit 2. Never result=pass. Never generate 500 photos on Linux in this leftover's default path.\n";
    s += "Add tests/desktop/desktop-500-gui-python.sh: fake tree with BOTH Scripts/python.exe and bin/python; assert --resolve-python prefers Scripts/python.exe. Drive the SHIPPED harness, do not reimplement the resolver in the test.\n";
    s += "Add packaging/scripts/stamp-desktop-500-gui-docs.py that can dry-run read a result.json (may no-op write if both-OS 500 JSON missing). Keep it rust-free.\n";
    s += "Keep tests/desktop/desktop-500-gui-linux.sh passing (exit 2 + skip is not pass).\n";
    s += "Wire python test into scripts/test-release-checks.sh as expect_success. Do NOT change the desktop.yml NSIS GUI awk yet.\n";
    s += "Run: bash tests/desktop/desktop-500-gui-linux.sh; bash tests/desktop/desktop-500-gui-python.sh; bash packaging/scripts/desktop-500-gui.sh --probe (expect 2 on Linux); npm run test:scripts.\n";
    s += "Commit subject exactly: ci: add packaged desktop ≥500 GUI harness script\n";
    s += github_tail();
    s += "Return ok=true only if linux host check and python discovery passed. stage=开发, commit=full sha, handoff=packaging/scripts/desktop-500-gui.sh, notes=summary.\n";
    s
}

fn develop3_prompt() {
    let s = "";
    s += "You are the 开发 Slice 3 agent for leftover #179. Minimal production QA gate. Work in /home/joe/repo/frame-pilot-desktop-500-gui. Do not edit desktop.yml. Do not tick §2.2.\n";
    s += repo_rules();
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'feat(desktop): gated QA path injection for unattended from-paths', do not redo. Return ok=true with that SHA.\n";
    s += "Read leftover plan section 7 and apps/desktop/src-tauri/src/sidecar.rs initialization_script_for_window and spawn_sidecar. Implement Path B:\n";
    s += "1) Fail-closed QA gate in Rust: inject window.__FRAMEPILOT_DESKTOP_QA__ only when FRAMEPILOT_DESKTOP_QA=1 AND every path is absolute AND under hard-coded prefix ($HOME/.cache/framepilot-desktop-500-gui or LOCALAPPDATA\\framepilot-desktop-500-gui) AND project root is not a parent of FRAMEPILOT_DATA_DIR. Preview window init script must NOT include the QA object even if env is set. Unit-test that.\n";
    s += "2) qa_write_evidence(line: String) command: only line arg; dest is startup-cached evidence path; reject newline; append+flush. ACL allow-qa-write-evidence in capabilities/default.json. Denied when QA off. Unit-test deny.\n";
    s += "3) spawn_sidecar env_remove all FRAMEPILOT_DESKTOP_QA* (keep existing FRAMEPILOT_PROJECT_ROOT_ALLOWLIST remove).\n";
    s += "4) apps/desktop/src/lib/desktopQaRunner.ts mounted in App.tsx as child of BrowserRouter, NOT in isPreviewWindow(). No-op unless desktop+main+valid QA object. Algorithm from leftover plan 7.2 using production api.registerDesktopProjectRoot and api.importPhotosFromPaths. Unit test that the runner module calls those names.\n";
    s += "5) Patch uvicorn access formatter in apps/api/app/sidecar_main.py formatters.access.fmt to include origin= and ua=. Missing headers as -. Test in test_sidecar_cli.py that fmt contains origin= and ua=.\n";
    s += "Do not bump APP_VERSION. Keep Linux harness skip-not-pass. Run cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib if rustc exists; otherwise still add the tests and run npm --prefix apps/desktop run test if present, plus npm --prefix apps/web run test:unit for any shared tests, plus pytest for sidecar_cli, plus bash linux host check.\n";
    s += "Commit subject exactly: feat(desktop): gated QA path injection for unattended from-paths\n";
    s += github_tail();
    s += "Return ok=true, stage=开发, commit=full sha, handoff=apps/desktop/src/lib/desktopQaRunner.ts, notes=summary.\n";
    s
}

fn develop4_prompt() {
    let s = "";
    s += "You are the 开发 Slice 4 agent for leftover #179. desktop.yml + test-release-checks together. Work in /home/joe/repo/frame-pilot-desktop-500-gui. Do not tick §2.2. Do not edit verify.yml.\n";
    s += repo_rules();
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'ci: run packaged ≥500 GUI probe and 500 after NSIS/DMG upload', do not redo. Return ok=true with that SHA.\n";
    s += "Read leftover plan section 8 and live .github/workflows/desktop.yml after 'Smoke packaged macOS DMG GUI launch'. Add probe+500 AFTER that existing smoke. Do not fold import into macos-dmg-gui-smoke.sh.\n";
    s += "Header rewrite: packaged GUI launch allowed for (a) existing macOS DMG install+run smoke and (b) packaging/scripts/desktop-500-gui.sh probe+500 against just-built NSIS/DMG. Still do not launch GUI from verify.yml.\n";
    s += "Steps: probe-windows if runner.os==Windows; probe-macos if always() && macOS; gui500-windows if always() && Windows && probe-windows success; gui500-macos if always() && macOS && probe-macos success. Job timeout-minutes 180. Probe step 10 min; 500 Windows 45 / macOS 40.\n";
    s += "Evidence uploads from $RUNNER_TEMP/desktop-500-gui/{mode}-{os}/ with distinct artifact names FramePilot-desktop-500-gui-probe-windows, ...-500-windows, ...-probe-macos, ...-500-macos. if: always() && runner.os. No photos.\n";
    s += "Rewrite scripts/test-release-checks.sh assertion 'desktop.yml does not launch packaged NSIS GUI' so it EXPECTS desktop-500-gui.sh on Windows and still forbids folding 500 into macos-dmg-gui-smoke.sh. Add awk that probe+500 sit after the macOS smoke step. Keep linux skip host check.\n";
    s += "Tick leftover-plan 开发 [x] (en+zh) in THIS commit. Do not tick §2.2. Do not tick 上线.\n";
    s += "Run npm run test:scripts until green. Run linux host check.\n";
    s += "Commit subject exactly: ci: run packaged ≥500 GUI probe and 500 after NSIS/DMG upload\n";
    s += github_tail();
    s += "Return ok=true, stage=开发, commit=full sha, handoff=.github/workflows/desktop.yml, notes=summary.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are the 测试 agent for leftover #179. Fail closed. Re-run checks yourself. Do not tick §2.2. Work in /home/joe/repo/frame-pilot-desktop-500-gui.\n";
    s += repo_rules();
    s += "1) git log origin/main..HEAD --format='%s' must contain Slice 2, 3, and 4 subjects.\n";
    s += "2) Run tests/desktop/desktop-500-gui-linux.sh TWICE; both must exit 0. Run packaging/scripts/desktop-500-gui.sh --probe TWICE; both must exit 2; output contains skip is not pass; no result=pass line.\n";
    s += "3) Run tests/desktop/desktop-500-gui-python.sh (must drive shipped --resolve-python).\n";
    s += "4) Run npm run test:scripts. Confirm desktop.yml probe+500 after macOS smoke and 500 is not folded into macos-dmg-gui-smoke.sh.\n";
    s += "5) Run npm run verify (symlink .venv/node_modules from /home/joe/repo/frame-pilot if missing). Must pass. Must not require rustc for verify.yml path.\n";
    s += "6) Confirm docs/desktop_development_plan.md §2.2 ≥500 still [ ]. Confirm verify.yml untouched.\n";
    s += "Tick leftover-plan 测试 [x] if checks passed. Commit only if you tick the board: subject docs: leftover packaged-desktop ≥500 GUI test record — or skip empty commit.\n";
    s += "Set passed=true only if you ran the checks and they succeeded. ok=true only if passed=true.\n";
    s += "Return stage=测试, commit=HEAD sha, handoff=docs/plans/2026-09-07-desktop-500-gui.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are the 上线 agent for leftover #179. Do not merge to main. Do not invent Phase 10. Work in /home/joe/repo/frame-pilot-desktop-500-gui.\n";
    s += repo_rules();
    s += "Confirm single draft PR #180. Comment on issue #179 that desktop.yml dispatch is starting. Do not close #144/#172/#177.\n";
    s += "Dispatch: gh workflow run desktop --repo joe-cheung-cae/frame-pilot --ref feature/desktop-500-gui\n";
    s += "Wait for the run with gh run watch --exit-status (long timeout; Windows+macOS Tauri often 20-45+ min plus 500 import). Do not declare pass from queued status.\n";
    s += "Inspect Windows and macOS jobs for probe and 500 steps / artifacts FramePilot-desktop-500-gui-500-windows and -macos. Read result.json if present.\n";
    s += "GREEN only if BOTH OS 500 result=pass (packaged WebView from-paths + culling preview, native dialog stubbed). Then commit subject exactly: docs: record packaged-desktop ≥500 GUI unattended pass\n";
    s += "That evidence commit MUST stamp living docs from JSON; tick docs/desktop_development_plan.md §2.2 ≥500 [x] with stub wording + both OS run URLs; bilingual desktop_testing header+subsection; leftover 上线 [x]. ISO-8601 with timezone.\n";
    s += "Update PR #180 body to Fixes #179 (keep Refs historical). Push.\n";
    s += "If either OS 500 is not pass: do NOT tick §2.2. Comment #179 with run URL and excerpt. Write oracle notes. Set ok=true still if you recorded the oracle honestly (DoD not claimed). notes must say DoD not claimed and which OS failed/skipped.\n";
    s += "Linux/WSL2 cannot launch NSIS/DMG; do not fake a local GUI pass.\n";
    s += "Do not merge.\n";
    s += "Return stage=上线, commit=HEAD sha, handoff=docs/plans/2026-09-07-desktop-500-gui.md, notes=PR URL, run URL, both-OS verdict.\n";
    s
}

let mode = "full";
if args != () && args.mode != () {
    mode = args.mode;
}

phase("Inspect");
log("Inspect leftover packaged-desktop ≥500 GUI progress");
let progress = agent(inspect_prompt(), inspect_opts("desktop-500-gui-inspect"));
if !stage_ok(progress) {
    await_user("verification", "Inspect failed. Resume to retry Inspect.");
    progress = agent(inspect_prompt(), inspect_opts("desktop-500-gui-inspect"));
}

if mode == "inspect-only" {
    complete(#{
        ok: true,
        task: "desktop-500-gui",
        notes: "inspect-only smoke path",
    });
}

let run_breakdown = true;
let run_review = true;
let run_archive = true;
let run_dev2 = true;
let run_dev3 = true;
let run_dev4 = true;
let run_test = true;
let run_launch = true;
if progress != () && progress.output != () {
    run_breakdown = should_run(progress.output.run_breakdown);
    run_review = should_run(progress.output.run_review);
    run_archive = should_run(progress.output.run_archive);
    run_dev2 = should_run(progress.output.run_dev2);
    run_dev3 = should_run(progress.output.run_dev3);
    run_dev4 = should_run(progress.output.run_dev4);
    run_test = should_run(progress.output.run_test);
    run_launch = should_run(progress.output.run_launch);
}

if run_breakdown {
    phase("需求拆解");
    log("需求拆解 already expected landed; inspect said it must run");
    await_user("verification", "需求拆解 should already be on feature/desktop-500-gui. Resume only if you really need to redo Slice 0.");
} else {
    log("Skipping 需求拆解 (already committed)");
}

if run_review {
    phase("评审");
    log("Leftover #179 评审");
    run_stage(review_prompt(), agent_opts("desktop-500-gui-review"), "评审 failed; inspect before 归档.");
    let sk = agent(skeptic_prompt(), skeptic_opts("desktop-500-gui-skeptic"));
    if !stage_ok(sk) {
        await_user("verification", "Skeptic agent failed. Resume to retry 评审.");
        sk = agent(skeptic_prompt(), skeptic_opts("desktop-500-gui-skeptic"));
    }
    if stage_ok(sk) && sk.output != () && sk.output.real == false {
        await_user("verification", "Skeptic set real=false. Resume only after the contract matches live code.");
    }
} else {
    log("Skipping 评审 (already committed)");
}

if run_archive {
    phase("归档");
    log("Leftover #179 归档");
    run_stage(archive_prompt(), agent_opts("desktop-500-gui-archive"), "归档 failed; inspect before 开发.");
} else {
    log("Skipping 归档 (already committed)");
}

if run_dev2 {
    phase("开发");
    log("Leftover #179 开发 Slice 2 harness");
    run_stage(develop2_prompt(), agent_opts("desktop-500-gui-dev2"), "Slice 2 failed; do not skip to Slice 3.");
} else {
    log("Skipping Slice 2 (already committed)");
}

if run_dev3 {
    phase("开发");
    log("Leftover #179 开发 Slice 3 QA gate");
    run_stage(develop3_prompt(), agent_opts("desktop-500-gui-dev3"), "Slice 3 failed; do not skip to Slice 4.");
} else {
    log("Skipping Slice 3 (already committed)");
}

if run_dev4 {
    phase("开发");
    log("Leftover #179 开发 Slice 4 desktop.yml");
    run_stage(develop4_prompt(), agent_opts("desktop-500-gui-dev4"), "Slice 4 failed; do not skip to 测试.");
} else {
    log("Skipping Slice 4 (already committed)");
}

if run_test {
    phase("测试");
    log("Leftover #179 测试");
    let test_r = run_stage(test_prompt(), test_opts("desktop-500-gui-test"), "测试 failed; do not 上线.");
    if !declared_passed(test_r) {
        await_user("verification", "Tests did not pass. Resume to retry 测试. Do not 上线.");
    }
} else {
    log("Skipping 测试 (already verified)");
}

let launch_r = ();
if run_launch {
    phase("上线");
    log("Leftover #179 上线 — desktop.yml oracle");
    launch_r = run_stage(launch_prompt(), agent_opts("desktop-500-gui-launch"), "上线 failed; do not tick §2.2 on a red/missing run.");
} else {
    log("Skipping 上线 (evidence commit already present)");
}

complete(#{
    ok: if run_launch { stage_ok(launch_r) && declared_ok(launch_r) } else { true },
    task: "desktop-500-gui",
    commit: if launch_r != () && launch_r.output != () { launch_r.output.commit } else { "" },
    notes: if launch_r != () && launch_r.output != () { launch_r.output.notes } else { "desktop-500-gui workflow finished" },
});
