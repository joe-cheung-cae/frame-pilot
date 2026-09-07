let meta = #{
    name: "macos-gui-dod",
    description: "Serial leftover pipeline: 需求拆解, 评审, 归档, 开发, 测试, 上线 for dual-platform installer GUI DoD",
    when_to_use: "Land leftover dual-platform installer GUI DoD (macOS DMG install+run) on feature/macos-gui-dod without inventing Phase 10",
    phases: [
        #{ title: "Inspect", detail: "Skip stages already committed and pushed" },
        #{ title: "需求拆解", detail: "Bilingual leftover plan + GitHub issue" },
        #{ title: "评审", detail: "Adversarial review against live tree and S9.12 skip" },
        #{ title: "归档", detail: "Confirm leftover board is ready for 开发" },
        #{ title: "开发", detail: "Darwin-only DMG GUI smoke + desktop.yml macOS step" },
        #{ title: "测试", detail: "Non-Darwin refusal, bash -n, npm run verify" },
        #{ title: "上线", detail: "Dispatch desktop.yml, record Darwin evidence, tick §2.2 only if green" },
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
            "run_develop": #{ "type": "boolean" },
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

fn subject_schedule() {
    "docs: schedule leftover macOS installer GUI DoD"
}

fn subject_review() {
    "docs: review leftover macOS installer GUI DoD"
}

fn subject_archive() {
    "docs: archive leftover macOS installer GUI DoD"
}

fn subject_develop() {
    "ci: smoke packaged macOS DMG GUI launch"
}

fn subject_evidence() {
    "docs: record dual-platform installer GUI DoD pass"
}

fn repo_rules() {
    let s = "";
    s += "Resolve the repo with: git rev-parse --show-toplevel. Do not hardcode machine home paths.\n";
    s += "ONE TASK ONLY: leftover dual-platform installer GUI DoD. Windows NSIS GUI pass is joe-cheung-cae/frame-pilot#144. S9.12 macOS DMG GUI lifecycle is joe-cheung-cae/frame-pilot#172 skip, not pass, dated 2026-09-05T12:31:10Z. Do not reopen #172. Do not invent Phase 10 / S10 / 2.3.\n";
    s += "Living session plan (read it): the user-approved leftover is install+run DoD, not a full S9.12 lifecycle re-run. Tick docs/desktop_development_plan.md section 2.2 installer row only after dated Darwin evidence from a green desktop.yml macOS GUI smoke.\n";
    s += "Plan files after 需求拆解: docs/plans/2026-09-07-macos-gui-dod.md and docs/plans/2026-09-07-macos-gui-dod.zh.md. Read both before later stages. Discover the GitHub issue number from that plan or gh; never guess the number.\n";
    s += "Branch must stay feature/macos-gui-dod. Create it from origin/main if missing. Do not checkout main for commits. Do not merge to main. Do not squash. Do not force-push.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, commits. Bilingual living docs when you touch docs. Local-first. Never modify or delete original photos. Do not commit camera photos, certs, or model weights.\n";
    s += "No cloud upload, login, payment, bundled neural models. Do not bump APP_VERSION. Do not sign. Do not claim Gatekeeper-clean or store listing. Do not tick packaged-desktop >=500 GUI.\n";
    s += "Do not re-run Windows NSIS GUI. Do not launch packaged GUI from verify.yml. npm run verify must stay rust-free.\n";
    s += "Scratch: mkdir -p \"$HOME/.cache/framepilot-macos-gui-dod\" && chmod 700 that directory. Never /tmp for secrets or QA photos. This leftover smoke does not import photos.\n";
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>'.\n";
    s += "Do not add Co-authored-by Cursor or similar trailers.\n";
    s += "YOU ARE NOT READ-ONLY. agent_type is general-purpose with capability_mode all. You have run_terminal_command, git, gh, search_replace, write, and GitHub MCP (search_tool then github__issue_write / create_pull_request). Do not return ok=false claiming plan mode, missing bash, missing gh, or missing issue_write. If a tool is missing, try the other (gh CLI or GitHub MCP) before failing.\n";
    s += "GITHUB: after every finished stage commit, git push -u origin HEAD. After the first successful push of this branch, if no open PR exists for head feature/macos-gui-dod against main, create ONE draft PR: title 'ci: macOS DMG installer GUI smoke (leftover DoD)'. Body must say Refs and the leftover issue number once it exists; must not say Fixes or Close until the evidence commit (上线) when desktop.yml macOS GUI smoke is green. Never open a second PR; later stages only push.\n";
    s += "Fallback: GitHub MCP create_pull_request with draft true. Never a second PR.\n";
    s += "Append SHA, subject, push result, and PR URL to $HOME/.cache/framepilot-macos-gui-dod/git-github.txt after every push.\n";
    s += "If push fails, capture the exact error, retry once, then continue the stage if possible and report the blocker in notes.\n";
    s
}

fn github_tail() {
    let s = "";
    s += "Then git push -u origin HEAD.\n";
    s += "Ensure a single draft PR exists for feature/macos-gui-dod into main (create if missing, never a second PR).\n";
    s += "Append SHA/subject/push/PR to $HOME/.cache/framepilot-macos-gui-dod/git-github.txt.\n";
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

fn plan_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: stage_schema(),
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
    s += "Inspect FramePilot leftover dual-platform installer GUI DoD progress. Use tools. Do not implement product code. Do not commit.\n";
    s += "Read: git rev-parse --show-toplevel; git rev-parse --abbrev-ref HEAD; git log origin/main..HEAD --oneline --format='%s'; uname -s; ";
    s += "develop_plan.md section 1.1; docs/desktop_development_plan.md section 2.2 and 5.6; docs/desktop_testing.md S9.12 subsection; ";
    s += ".github/workflows/desktop.yml header and macOS job (does it launch the packaged DMG GUI today?); ";
    s += "docs/plans/2026-09-07-macos-gui-dod.md if it exists.\n";
    s += "Search git log origin/main..HEAD for these exact subjects and set run_* false when that commit already exists, true when the agent must still do the work:\n";
    s += "run_breakdown false if subject 'docs: schedule leftover macOS installer GUI DoD' exists.\n";
    s += "run_review false if subject 'docs: review leftover macOS installer GUI DoD' exists.\n";
    s += "run_archive false if subject 'docs: archive leftover macOS installer GUI DoD' exists.\n";
    s += "run_develop false if subject 'ci: smoke packaged macOS DMG GUI launch' exists.\n";
    s += "run_test true unless the develop subject exists AND you have evidence npm run verify was already run green for that SHA in notes; when unsure set true.\n";
    s += "run_launch false if subject 'docs: record dual-platform installer GUI DoD pass' exists.\n";
    s += "If docs/desktop_development_plan.md section 2.2 installer row is already [x] with a Darwin CI pointer, still set run_launch false only when the evidence commit exists.\n";
    s += "issue: leftover GitHub issue number as a string if the plan or gh issue list shows it, else empty string. Do not guess.\n";
    s += "notes: branch, uname, whether desktop.yml already smokes DMG GUI, and next stage.\n";
    s
}

fn breakdown_prompt() {
    let s = "";
    s += "You are the 需求拆解 agent for FramePilot leftover dual-platform installer GUI DoD. Documentation contract only. Do not implement the smoke script or edit desktop.yml yet.\n";
    s += repo_rules();
    s += "You MUST: (1) create or reuse the leftover GitHub issue, (2) checkout feature/macos-gui-dod, (3) write/update bilingual plans with the real issue number, (4) git add/commit/push, (5) open the single draft PR. Return ok=false only after those commands failed, not because you think you lack tools.\n";
    s += "Create and checkout feature/macos-gui-dod from origin/main if needed.\n";
    s += "Untracked drafts may already exist at docs/plans/2026-09-07-macos-gui-dod.md and the zh counterpart with placeholder #N. Reuse them. After issue create, replace #N with the real number in both files. Do not leave a placeholder.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md section 1.1, docs/desktop_development_plan.md section 2.2 and 5.6, docs/desktop_testing.md (S9.12 results and record template), ";
    s += "docs/v2_known_limitations.md desktop bullets, README desktop paragraph, .github/workflows/desktop.yml, .github/workflows/verify.yml, ";
    s += "apps/desktop/src-tauri/tauri.conf.json productName/window title, apps/desktop/src-tauri/src/sidecar.rs ready-line and sidecar.log path, packaging/scripts/stage-sidecar.sh.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: schedule leftover macOS installer GUI DoD', do not redo. Return ok=true with that SHA.\n";
    s += "GitHub issue: first run gh issue list --repo joe-cheung-cae/frame-pilot --state open and --state all --limit 30. Search for an existing leftover installer GUI DoD issue. If none, create ONE with gh issue create --repo joe-cheung-cae/frame-pilot, or GitHub MCP github__issue_write method=create owner=joe-cheung-cae repo=frame-pilot. ";
    s += "Title exactly: Leftover: dual-platform installer GUI DoD (macOS DMG install+run). ";
    s += "Body must say: Windows pass is #144; S9.12 #172 is skip not pass at 2026-09-05T12:31:10Z; implement CI same-job DMG attach+launch+loopback GET /health; tick section 2.2 only with dated Darwin evidence; out: Phase 10, packaged-desktop >=500 GUI, signing, Windows re-run, full quit+job matrix, APP_VERSION bump. Use the number GitHub returns. Write owner/repo#N in the plan. Do not guess the number before create.\n";
    s += "Write bilingual leftover plan docs/plans/2026-09-07-macos-gui-dod.md and docs/plans/2026-09-07-macos-gui-dod.zh.md. Each English page links to the Chinese counterpart near the top and vice versa. Include: why leftover not Phase 10; locked decisions from this prompt; status board with 需求拆解/评审/归档/开发/测试/上线 plus smoke-landed vs DoD-ticked; smoke script contract; desktop.yml macOS-only wiring; tick rules; non-goals; file map.\n";
    s += "Status board: tick 需求拆解 [x] in this commit only. Leave 开发 and DoD-ticked [ ].\n";
    s += "If .grok/workflows/macos-gui-dod.rhai exists, include it in this commit.\n";
    s += "Commit subject exactly: docs: schedule leftover macOS installer GUI DoD\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += github_tail();
    s += "Return ok=true, stage=需求拆解, commit=full sha, handoff=docs/plans/2026-09-07-macos-gui-dod.md, notes=issue number, PR URL, contract summary.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are the 评审 agent for FramePilot leftover dual-platform installer GUI DoD. Adversarially review the leftover plan against the live tree. Do not implement the smoke script or desktop.yml yet.\n";
    s += repo_rules();
    s += "You have git and gh. Stay on feature/macos-gui-dod. Commit and push if you change the bilingual plan; otherwise skip an empty commit and still return ok=true.\n";
    s += "Read docs/plans/2026-09-07-macos-gui-dod.md (+ zh), develop_plan.md section 1.1, docs/desktop_development_plan.md section 2.2, docs/desktop_testing.md S9.12, .github/workflows/desktop.yml, .github/workflows/verify.yml, sidecar ready-line code.\n";
    s += "Confirm: DoD is install+run not full lifecycle; skip is not pass; verify.yml stays rust-free; smoke is Darwin-only; same-job DMG not a downloaded artifact; Windows not re-run; no Phase 10; section 2.2 must not be ticked in the 开发 commit; issue number in the plan matches gh.\n";
    s += "Fix bilingual plan holes only if the live tree makes the spec wrong. Do not tick 开发 or DoD.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: review leftover macOS installer GUI DoD', do not redo. Return ok=true with that SHA.\n";
    s += "Commit subject exactly: docs: review leftover macOS installer GUI DoD\n";
    s += "If nothing is staged, skip an empty commit and still return ok=true.\n";
    s += github_tail();
    s += "Return ok=true, stage=评审, commit=HEAD sha, handoff=docs/plans/2026-09-07-macos-gui-dod.md, notes=review summary.\n";
    s
}

fn skeptic_prompt() {
    let s = "";
    s += "You are a read-only skeptic for leftover dual-platform installer GUI DoD. Use grep/read_file/gh. Do not edit.\n";
    s += "Confirm with evidence (file:line or issue URL) ALL of: (1) docs/desktop_development_plan.md section 2.2 installer row is still [ ] OR already ticked only with Darwin evidence; (2) docs/desktop_testing.md S9.12 verdict is skip not pass; (3) .github/workflows/desktop.yml currently does not launch packaged NSIS/DMG GUI unless this branch already added the smoke; (4) verify.yml does not launch a DMG; (5) uname on this host is not Darwin, so local pass is impossible; (6) this leftover is the right next slice per develop_plan.md section 1.1 and must not invent Phase 10; (7) originals are not modified by this leftover.\n";
    s += "Set real=true only with evidence you independently read. Set ok=true if this leftover is still the right next slice. notes=short. evidence=file:line citations.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are the 归档 agent for FramePilot leftover dual-platform installer GUI DoD. Do not implement the smoke script yet.\n";
    s += repo_rules();
    s += "Read docs/plans/2026-09-07-macos-gui-dod.md section status board. 开发 must still be [ ] unless subject 'ci: smoke packaged macOS DMG GUI launch' already exists (idempotent).\n";
    s += "Record that 开发 MUST land the smoke script + desktop.yml macOS step, tick leftover-plan 开发 [x] in that same commit, push, and must NOT tick docs/desktop_development_plan.md section 2.2 yet.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: archive leftover macOS installer GUI DoD', do not redo. Return ok=true with that SHA.\n";
    s += "Commit subject exactly: docs: archive leftover macOS installer GUI DoD\n";
    s += "If nothing is staged, skip an empty commit and return ok=true.\n";
    s += github_tail();
    s += "Return ok=true, stage=归档, commit=HEAD sha, handoff=docs/plans/2026-09-07-macos-gui-dod.md, notes=ready for 开发.\n";
    s
}

fn develop_prompt() {
    let s = "";
    s += "You are the 开发 agent for FramePilot leftover dual-platform installer GUI DoD. Tests first, then the smoke script and desktop.yml. Do not tick docs/desktop_development_plan.md section 2.2. Do not start 上线 CI dispatch.\n";
    s += repo_rules();
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'ci: smoke packaged macOS DMG GUI launch', do not redo implementation. Return ok=true with that SHA.\n";
    s += "TESTS FIRST. Add tests/desktop/macos-dmg-gui-smoke-nondarwin.sh (or equivalent) that runs packaging/scripts/macos-dmg-gui-smoke.sh on this host and asserts non-zero exit AND stdout/stderr contains 'skip is not pass'. Watch it fail because the smoke script is missing, then implement the smoke script so the host check passes on Linux.\n";
    s += "Create packaging/scripts/macos-dmg-gui-smoke.sh with set -euo pipefail. Darwin-only for the attach/launch path. Required behavior:\n";
    s += "1) If uname -s is not Darwin, print that skip is not pass, exit non-zero (use 2). Never print pass on Linux.\n";
    s += "2) Require a .dmg path argument. hdiutil attach -nobrowse. Copy FramePilot.app to a throwaway directory under $HOME/.cache/framepilot-macos-gui-dod (not /tmp). xattr -cr the copy. open the .app.\n";
    s += "3) Poll up to 30s (one retry of open if needed) for sidecar ready: parse ~/Library/Application Support/FramePilot/logs/sidecar.log for 'FRAMEPILOT_API ready host=127.0.0.1 port=<n>' OR lsof listen of framepilot-api on 127.0.0.1. Reject 0.0.0.0. Never hardcode ports 8000/6300.\n";
    s += "4) GET http://127.0.0.1:<n>/health must be 200 JSON with version and service. Print APP_VERSION.\n";
    s += "5) Best-effort window title FramePilot via lsappinfo or osascript. If that fails, record title_ok=false with the exact error; still pass the smoke if process+health succeeded.\n";
    s += "6) Quit the app; wait; no leftover framepilot-api LISTEN (TIME_WAIT ok). hdiutil detach. Delete the copied .app. Data directory may remain.\n";
    s += "7) Print a machine-readable summary: os, utc ISO-8601 timestamp with Z, health json, port, title_ok, result=pass.\n";
    s += "Do not import photos. Do not automate quit+import/processing/export dialogs.\n";
    s += "Wire into .github/workflows/desktop.yml macOS job only, after npx tauri build --bundles dmg, against the just-built apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg. ";
    s += "Update the desktop.yml header: packaged GUI launch is allowed on macOS for this smoke; still do not launch NSIS; still do not launch GUI from verify.yml.\n";
    s += "Prefer zero Rust/Python/TypeScript production edits. Do not edit verify.yml. Do not add Playwright GUI. Do not add pytest that opens a WebView.\n";
    s += "Tick leftover plan 开发 [x] (en+zh) in the SAME commit. Do not tick section 2.2. Do not tick DoD-ticked on the leftover board.\n";
    s += "Run the non-Darwin host check until it exits 0. Run bash -n on the smoke script. If shellcheck exists, run it. Do not run npm run verify in a way that requires rustc.\n";
    s += "Commit subject exactly: ci: smoke packaged macOS DMG GUI launch\n";
    s += "Include tests, smoke script, desktop.yml, leftover plan ticks in that commit.\n";
    s += github_tail();
    s += "Return ok=true only if the named host check passed and the commit exists. stage=开发, commit=full sha, handoff=docs/plans/2026-09-07-macos-gui-dod.md, notes=summary including PR URL.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are the 测试 agent for FramePilot leftover dual-platform installer GUI DoD. Fail closed. Re-run checks yourself. Do not dispatch desktop.yml. Do not tick section 2.2.\n";
    s += repo_rules();
    s += "1) git log origin/main..HEAD --format='%s' must contain 'ci: smoke packaged macOS DMG GUI launch'.\n";
    s += "2) Re-run tests/desktop/macos-dmg-gui-smoke-nondarwin.sh (or the host check added in 开发) and confirm exit 0. Re-run bash -n packaging/scripts/macos-dmg-gui-smoke.sh.\n";
    s += "3) Run npm run verify. It must stay rust-free, must not require rustc/cargo/tauri, must not attach a DMG. If verify is too long, still run it; do not skip.\n";
    s += "4) git diff origin/main...HEAD --stat must stay inside this leftover file map: leftover plan md+zh, smoke script, host check, desktop.yml, .grok/workflows/macos-gui-dod.rhai, bilingual docs only if already required by 需求拆解. No original photos, certs, or model weights.\n";
    s += "5) Confirm docs/desktop_development_plan.md section 2.2 installer row is still [ ] on this branch.\n";
    s += "Set passed=true only if you ran the checks and they succeeded. ok=true only if passed=true and scope is clean.\n";
    s += "If tests fail, fix only this leftover's files, keep one logical develop commit (amend only if HEAD is the develop commit and not yet depended on), re-run.\n";
    s += "Return stage=测试, commit=HEAD sha, handoff=docs/plans/2026-09-07-macos-gui-dod.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are the 上线 agent for FramePilot leftover dual-platform installer GUI DoD. Do not merge to main. Do not invent Phase 10.\n";
    s += repo_rules();
    s += "Confirm git status clean except untracked noise. Confirm push happened. Confirm the single draft PR exists (create if missing).\n";
    s += "Read the leftover plan for the GitHub issue number. Comment on that issue with 开发 SHA and that desktop.yml dispatch is starting. Do not close #172 or #144.\n";
    s += "Dispatch CI: gh workflow run desktop --repo joe-cheung-cae/frame-pilot --ref feature/macos-gui-dod\n";
    s += "Then find the run id and wait until the macOS job is terminal. Use gh run watch --exit-status with a long timeout (desktop Windows+macOS Tauri builds often take 20-45 minutes). If the command is backgrounded, wait for it; do not busy-sleep in a loop of sleep 1. Do not declare pass from queued status.\n";
    s += "Read the macOS job logs for the GUI smoke step. Extract APP_VERSION, port, health JSON, title_ok, utc timestamp.\n";
    s += "GREEN path: only if the macOS GUI smoke step exited 0 and GET /health returned version+service from the packaged app. Then commit subject exactly: docs: record dual-platform installer GUI DoD pass\n";
    s += "That evidence commit MUST: add a NEW dated results subsection in docs/desktop_testing.md (+ zh) keeping the S9.12 skip subsection as history; tick docs/desktop_development_plan.md section 2.2 installer row [x] with Windows #144 plus this leftover issue plus the Actions run URL; update section 5.6 packaged macOS GUI pass target to this leftover [x] for install+run DoD and note full quit+job matrix still unscheduled; update develop_plan.md section 1.1 (+ zh), docs/v2_known_limitations.md (+ zh), README.md (+ zh), CHANGELOG Unreleased (+ zh), implement_goals.md (+ zh), leftover plan DoD-ticked [x] and 上线 [x]. Use ISO-8601 timestamps with timezone (UTC Z is fine). Do not tick packaged-desktop >=500.\n";
    s += "Update the draft PR body to Fixes the leftover issue (keep Refs for #144/#172 as historical, never Fixes #172).\n";
    s += "RED or skip path: do NOT tick section 2.2. Comment the leftover issue with run URL and failure excerpt. Set ok=false. notes must say DoD not claimed.\n";
    s += "After the evidence commit (green only), git push -u origin HEAD and comment the leftover issue with full SHA, run URL, APP_VERSION, timestamp.\n";
    s += "Do not merge. Do not close #172.\n";
    s += "Return ok=true only if Darwin smoke was green AND the evidence commit exists AND section 2.2 is [x]. stage=上线, commit=full sha, handoff=docs/plans/2026-09-07-macos-gui-dod.md, notes=PR URL, run URL, APP_VERSION.\n";
    s
}

phase("Inspect");
log("Inspect leftover macOS installer GUI DoD progress");
let progress = agent(inspect_prompt(), inspect_opts("macos-gui-dod-inspect"));
if !stage_ok(progress) {
    await_user("verification", "Inspect failed. Resume to retry Inspect. Do not skip to 需求拆解.");
    progress = agent(inspect_prompt(), inspect_opts("macos-gui-dod-inspect"));
}

let run_breakdown = true;
let run_review = true;
let run_archive = true;
let run_develop = true;
let run_test = true;
let run_launch = true;
if progress != () && progress.output != () {
    run_breakdown = should_run(progress.output.run_breakdown);
    run_review = should_run(progress.output.run_review);
    run_archive = should_run(progress.output.run_archive);
    run_develop = should_run(progress.output.run_develop);
    run_test = should_run(progress.output.run_test);
    run_launch = should_run(progress.output.run_launch);
}

if !run_breakdown && !run_review && !run_archive && !run_develop && !run_test && !run_launch {
    complete(#{
        ok: true,
        task: "macos-gui-dod",
        notes: "All stages already committed; nothing to run.",
    });
}

let breakdown_r = ();
if run_breakdown {
    phase("需求拆解");
    log("Leftover macOS GUI DoD 需求拆解");
    breakdown_r = run_stage(breakdown_prompt(), plan_opts("macos-gui-dod-breakdown"), "需求拆解 failed; inspect before 评审.");
} else {
    log("Skipping 需求拆解 (already committed)");
}

if run_review {
    phase("评审");
    log("Leftover macOS GUI DoD 评审");
    run_stage(review_prompt(), plan_opts("macos-gui-dod-review"), "评审 failed; inspect before 归档.");
    let sk = agent(skeptic_prompt(), skeptic_opts("macos-gui-dod-skeptic"));
    if !stage_ok(sk) {
        await_user("verification", "Skeptic agent failed. Resume to retry 评审. Do not skip to 开发.");
        sk = agent(skeptic_prompt(), skeptic_opts("macos-gui-dod-skeptic"));
    }
    if stage_ok(sk) && sk.output != () && sk.output.real == false {
        await_user("verification", "Skeptic set real=false. Resume only after the contract matches live code.");
    }
} else {
    log("Skipping 评审 (already committed)");
}

if run_archive {
    phase("归档");
    log("Leftover macOS GUI DoD 归档");
    run_stage(archive_prompt(), agent_opts("macos-gui-dod-archive"), "归档 failed; inspect before 开发.");
} else {
    log("Skipping 归档 (already committed)");
}

if run_develop {
    phase("开发");
    log("Leftover macOS GUI DoD 开发");
    run_stage(develop_prompt(), agent_opts("macos-gui-dod-develop"), "开发 failed; inspect before 测试. Do not skip the GitHub push.");
} else {
    log("Skipping 开发 (already committed)");
}

if run_test {
    phase("测试");
    log("Leftover macOS GUI DoD 测试");
    let test_r = run_stage(test_prompt(), test_opts("macos-gui-dod-test"), "测试 failed; do not 上线.");
    if !declared_passed(test_r) {
        await_user("verification", "Tests did not pass. Resume to retry 测试. Do not 上线.");
    }
} else {
    log("Skipping 测试 (already verified)");
}

let launch_r = ();
if run_launch {
    phase("上线");
    log("Leftover macOS GUI DoD 上线 — dispatch desktop.yml and wait for macOS GUI smoke");
    launch_r = run_stage(launch_prompt(), agent_opts("macos-gui-dod-launch"), "上线 failed; inspect git push, desktop.yml run, and issue comment. Do not tick section 2.2 on a red run.");
} else {
    log("Skipping 上线 (evidence commit already present)");
}

complete(#{
    ok: if run_launch { stage_ok(launch_r) && declared_ok(launch_r) } else { true },
    task: "macos-gui-dod",
    commit: if launch_r != () && launch_r.output != () { launch_r.output.commit } else { "" },
    notes: if launch_r != () && launch_r.output != () { launch_r.output.notes } else { "macos-gui-dod workflow finished" },
});
