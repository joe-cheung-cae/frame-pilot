let meta = #{
    name: "desktop-review-fix",
    description: "Serial sidecar-lifecycle and quit-handshake review-fix pipeline on feature/desktop-packaging: 需求拆解, 评审, 归档, 开发, 测试, 上线",
    when_to_use: "Fix confirmed desktop code-review findings F001-F006 (joe-cheung-cae/frame-pilot#33 #35 #36 #34 #31 #32) without starting Phase 2",
    phases: [
        #{ title: "需求拆解", detail: "Docs-only breakdown of in-scope review-fix findings" },
        #{ title: "评审", detail: "Adversarial review of the breakdown against live lib.rs and sidecar.rs" },
        #{ title: "归档", detail: "Archive the accepted review-fix backlog with A-D slices" },
        #{ title: "开发", detail: "Tests-first serial slices A then B then C then D" },
        #{ title: "测试", detail: "cargo, test:web, rust-free verify, optional desktop smoke" },
        #{ title: "上线", detail: "Handoff, GitHub comments, push; do not open a PR or close issues" },
    ],
};

fn stage_schema() {
    #{
        "type": "object",
        "properties": #{
            "ok": #{ "type": "boolean" },
            "stage": #{ "type": "string" },
            "commit": #{ "type": "string" },
            "handoff": #{ "type": "string" },
            "notes": #{ "type": "string" },
            "verdict": #{ "type": "string" },
        },
    }
}

fn repo_path() {
    "/Users/chao/workspace/repo/frame-pilot"
}

fn scratch_path() {
    "/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-501/desktop-review-fix"
}

fn evidence_path() {
    "/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-7cc6541d0495/implementer"
}

fn shared_rules() {
    let s = "";
    s += "docs/handoff is retired. Do not create, write, or restore any docs/handoff/* file (including STATUS.md). The living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Phase 0-2 are already on main; remaining work is Phase 3-5. Do not retick completed Phase 0-2 boxes. Do not write docs/handoff/STATUS.md.\n";
    s += "Repo: " + repo_path() + "\n";
    s += "Scratch (chmod 700, never shared /tmp): " + scratch_path() + "\n";
    s += "Also copy every capture named below into " + evidence_path() + " after writing it.\n";
    s += "mkdir -p both scratch dirs if missing; chmod 700 " + scratch_path() + ".\n";
    s += "Branch MUST stay feature/desktop-packaging. Confirm with git rev-parse --abbrev-ref HEAD before committing.\n";
    s += "Do not checkout other branches. Do not open a pull request. Do not merge to main. Do not close GitHub issues.\n";
    s += "THIS OBJECTIVE REQUIRES git push after every finished stage AND after every 开发 slice commit. Use: git push -u origin HEAD\n";
    s += "If push fails, write the exact git error to " + scratch_path() + "/git-push.txt and still finish the product work.\n";
    s += "After every push, append git log --oneline origin/main..HEAD and git status -sb to " + scratch_path() + "/git-stage-commits.txt and copy that file to evidence.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory. Do not invent issue numbers. Always write owner/repo#N.\n";
    s += "English for code, comments, tests, docs, commits. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not start desktop Phases 2-5. Do not bump APP_VERSION. Do not redo D1.01-D1.09 product work.\n";
    s += "Do not set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME. Keep apps/web on Next.js. Do not add output: export.\n";
    s += "npm run verify must not install or require rustc, cargo, or Tauri.\n";
    s += "Sidecar binds 127.0.0.1 only. Absolute --data-dir. Shipped spawn never --port 0.\n";
    s += "Import cancel stays cooperative: POST cancel, in-flight photo may remain processing until retry. Do not weaken test_cancelled_import_job_stops_safely_and_retry_preserves_review_state.\n";
    s += "Quit-anyway / SIGTERM is failed + retryable via fail_active_jobs_on_startup, not cancelled. Processing jobs have no cancel route. Import-only extra button.\n";
    s += "Do not add Co-authored-by Cursor or similar trailers.\n";
    s += "F001 (joe-cheung-cae/frame-pilot#33) and F006 (joe-cheung-cae/frame-pilot#32) are ONE implementation. Do not write a second patch for F006.\n";
    s += "Never leave an orphan sidecar after start failure, retry, or quit.\n";
    s += "If nothing is staged, skip an empty commit. Do not recreate docs/handoff files.\n";
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

fn review_is_reject(r) {
    if !stage_ok(r) {
        return false;
    }
    let out = r.output;
    if out == () {
        return false;
    }
    if type_of(out) == "string" {
        return false;
    }
    out.verdict == "reject"
}

fn breakdown_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, plan-oriented) for stage 需求拆解.\n";
    s += shared_rules();
    s += "This stage is documentation only. Do not implement production Rust/TS/Python. You MAY git-add the already-authored workflow file.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md, docs/desktop_goal_mode.md, ";
    s += "docs/plans/2026-08-18-desktop-packaging.md (D1.09 and section 5.1 — Phase 1 boxes are already [x]; do not retick them), ";
    s += "docs/plans/2026-08-18-desktop-packaging.md, docs/v2_known_limitations.md, docs/desktop_feasibility_notes.md, ";
    s += "apps/desktop/src-tauri/src/lib.rs, apps/desktop/src-tauri/src/sidecar.rs, ";
    s += "apps/desktop/src-tauri/Cargo.toml (crate name framepilot-desktop, lib framepilot_desktop_lib).\n";
    s += "Read GitHub via gh: joe-cheung-cae/frame-pilot#30 (parent, verdict block, HEAD 7e545f80), ";
    s += "#33 F001 high, #35 F002 high, #36 F003 high, #34 F004 medium, #31 F005 medium, #32 F006 medium (same as F001). ";
    s += "Do not invent issue numbers. Always write owner/repo#N.\n";
    s += "Confirm git branch is feature/desktop-packaging and repo is " + repo_path() + ".\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "(joe-cheung-cae/frame-pilot#33 #35 #36 #34 #31 #32 and parent #30), out-of-scope ";
    s += "(Phases 2-5, APP_VERSION bump, PR/merge, closing issues, D1.01-D1.09 redo, cloud/login/payment, HEIC/RAW/XMP, bundled models, ";
    s += "output: export, FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME, a second F006 patch), files, tests-first list, ";
    s += "acceptance boxes COPIED from #33 #35 #36 #34 #31 #32, and risks.\n";
    s += "State explicitly: F001==F006 one change; F003 is import-only (processing extra_button is empty and still parses); ";
    s += "F003+F004 must land together; ExitRequested needs prevent_exit; npm run verify stays rust-free.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "parent issue joe-cheung-cae/frame-pilot#30, in-scope sub-issues listed, tests_run=none (docs), ";
    s += "timestamp as ISO-8601 with timezone (run date '+%Y-%m-%dT%H:%M:%S%z' and format offset as +08:00 not +0800; never date-only).\n";
    s += "If .grok/workflows/desktop-review-fix.rhai exists, include it in this commit. Do not add desktop-packaging-review.rhai.\n";
    s += "Commit message exactly: docs: break down desktop review-fix requirements\n";
    s += "Then git push -u origin HEAD. Append log+status to scratch git-stage-commits.txt.\n";
    s += "Return stage=需求拆解, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary. Set verdict only if needed; do not set verdict=reject.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, plan-oriented, adversarial) for stage 评审.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-08-18-desktop-packaging.md, docs/plans/2026-08-18-desktop-packaging.md, live apps/desktop/src-tauri/src/lib.rs and sidecar.rs, ";
    s += "and the GitHub issue bodies for joe-cheung-cae/frame-pilot#33 #35 #36 #34 #31 #32.\n";
    s += "Confirm against the live code, not the docs alone:\n";
    s += "1) F001==F006: lib.rs start_sidecar_process wait_for_ready_line ? and missing stdout drop Child without terminate_sidecar; health-fail path already terminates; retry reuses port and data-dir. One terminate-on-error + wait path. Also store_child must not keep a child if shutdown is set.\n";
    s += "2) F003 is import-only: extra_button for Import is a regular Rust string with real ASCII quotes interpolated into a double-quoted JS innerHTML assignment inside a raw string; Processing extra_button is empty so that script still parses. quit_dialog_script_hides_cancel_for_processing_jobs is substring-only and cannot catch this.\n";
    s += "3) F003+F004 must land together: today F003 makes F004 the live import-close path (2s timeout then unwrap_or CancelAndQuit).\n";
    s += "4) ExitRequested needs prevent_exit: app.run matches Exit | ExitRequested and always request_shutdown(); matches! discards ExitRequestApi.\n";
    s += "5) npm run verify must stay rust-free (package.json verify script must not grow rustc/cargo/tauri).\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Reject ONLY if the breakdown contradicts locked decisions or the live defects. Missing-but-fixable nits are accept-with-notes, not reject. If you reject, still write the review file and STATUS, commit and push, and set structured verdict=reject.\n";
    s += "Do not write STATUS.md; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not retick completed Phase 0-2 boxes.\n";
    s += "Commit message exactly: docs: review desktop review-fix requirements\n";
    s += "Then git push -u origin HEAD. Append log+status to scratch.\n";
    s += "Return stage=评审, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary, verdict=accept-with-notes or reject.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are grok-4.6 (low effort, general-purpose) for stage 归档.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-08-18-desktop-packaging.md and docs/plans/2026-08-18-desktop-packaging.md. Proceed only if 评审 did not reject.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "depends-on, files, implement, tests-first, commit-hint, done-when.\n";
    s += "Slice 开发 as exactly:\n";
    s += "A. F001+F006 terminate-on-error (and missing stdout). Commit: desktop: terminate sidecar on ready-line failure\n";
    s += "B. F002 shutdown-aware supervisor / store_child / Drop. Commit: desktop: avoid sidecar respawn after shutdown. Do not start B before A is committed.\n";
    s += "C. F003+F004 parseable import overlay + Stay fallback. Commit: desktop: fix import quit dialog script and stay fallback. Do not start C before B is committed.\n";
    s += "D. F005 ExitRequested prevent_exit + same close_decision. Commit: desktop: route app quit through the close dialog. Do not start D before C is committed.\n";
    s += "State that extra per-slice commits are allowed, 开发 must finish with those four required subjects (STATUS may be updated in D), and F006 is not a second feature.\n";
    s += "Do not write STATUS.md; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1.\n";
    s += "Commit message exactly: docs: archive accepted desktop review-fix backlog\n";
    s += "Then git push -u origin HEAD. Append log+status to scratch.\n";
    s += "Return stage=归档, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn develop_a_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 slice A: F001+F006 (joe-cheung-cae/frame-pilot#33 and #32).\n";
    s += shared_rules();
    s += "Do not start slices B/C/D. Tests first. Drive shipped functions. Do not mock the unit under test. Do not re-implement the oracle in the test.\n";
    s += "Read docs/plans/2026-08-18-desktop-packaging.md, lib.rs start_sidecar_process (~66-76), start_sidecar_with_retry, store_child, sidecar.rs spawn/wait/terminate.\n";
    s += "Problem: after spawn_sidecar, wait_for_ready_line ? and missing stdout drop Child without terminate_sidecar. std::process::Child drop does not kill. Retry reuses the same loopback port and --data-dir.\n";
    s += "Implement ONE terminate-on-error + wait path that also covers missing stdout. Prefer a Drop/guard so every post-spawn Err path terminates (including wait_for_ready_line timeout/parse failure). Health-fail already terminates; keep that. If shutdown is already set after a restart spawn, terminate the new child instead of store_child — implement that store_child check here so F006 is closed with F001; do not write a second later patch for F006.\n";
    s += "Required tests (add more if needed) in apps/desktop/src-tauri, same #[cfg(test)] style as sidecar.rs:\n";
    s += "- After a ready-line timeout or parse failure, terminate_sidecar (and wait) ran; retry can bind the same allocated loopback port; no leftover listener.\n";
    s += "- Missing stdout also terminates the child before return.\n";
    s += "Spawn a real child (for example a short listener or sleep) rather than mocking Child. Prefer extracting a small testable guard into sidecar.rs if lib.rs is awkward to unit-test without Tauri.\n";
    s += "Do not change apps/web except if a shared string is truly required (it should not be). Do not weaken import-cancel tests. Do not bump APP_VERSION.\n";
    s += "Run cargo test in apps/desktop/src-tauri (crate framepilot-desktop) until green. Capture " + scratch_path() + "/cargo-test-A.txt and copy to evidence.\n";
    s += "If rustc/cargo is missing (exit 127), capture exact command+error to " + scratch_path() + "/tauri-toolchain.txt, do not claim tests passed, still keep the code, and return success=false notes.\n";
    s += "Commit message exactly: desktop: terminate sidecar on ready-line failure\n";
    s += "Push. Return stage=开发-A, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn develop_b_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 slice B: F002 (joe-cheung-cae/frame-pilot#35).\n";
    s += shared_rules();
    s += "Slice A MUST already be committed on feature/desktop-packaging. Do not start C/D. Tests first. Drive shipped functions.\n";
    s += "Read lib.rs SidecarState, store_child, request_shutdown, supervise_sidecar, start_sidecar_process.\n";
    s += "Problem: supervise_sidecar only checks shutdown before sleep and before probe_health. Close during the 400ms probe looks like health failure, recovery_action Restart, start_sidecar_process runs after the old child was taken, store_child does not re-check shutdown. New process can outlive window destroy.\n";
    s += "Implement: re-check shutdown after probe_health and immediately before start_sidecar_process and store_child. If shutdown is set, do not spawn; terminate any local Child. Prefer SidecarState Drop that always terminates. store_child may already terminate-on-shutdown from slice A; keep that and add supervisor re-checks + Drop.\n";
    s += "Required tests: if shutdown is set, start_sidecar_process/store_child do not keep a live child. Re-check after probe_health. cargo test in apps/desktop/src-tauri until green. Capture " + scratch_path() + "/cargo-test-B.txt.\n";
    s += "Do not change apps/web. Do not bump APP_VERSION. Do not start Phase 2.\n";
    s += "Commit message exactly: desktop: avoid sidecar respawn after shutdown\n";
    s += "Push. Return stage=开发-B, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn develop_c_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 slice C: F003+F004 together (joe-cheung-cae/frame-pilot#36 and #34).\n";
    s += shared_rules();
    s += "Slice B MUST already be committed. Do not start D. Tests first. Drive shipped functions. A substring-only test is NOT enough for import.\n";
    s += "F003: quit_dialog_script in sidecar.rs. Import extra_button is a regular Rust string with real ASCII quotes, interpolated into a double-quoted JS innerHTML assignment inside a raw string. Generated import script is a SyntaxError. Overlay never mounts. Processing extra_button is empty, so that path still parses. Fix generation (DOM APIs, HTML entities, or the same backslash-quote escaping as the hardcoded buttons).\n";
    s += "F004: handle_close_requested in lib.rs ~130-146. If dialog_shown does not arrive within 2s, unwrap_or(CloseChoice::CancelAndQuit) POSTs cancel without confirmation. Change unconfirmed handshake to CloseChoice::Stay and reset close_in_progress. CancelAndQuit only for an explicit button payload. Extract a small testable helper (for example unresolved handshake -> Stay) so tests drive shipped logic without a WebView.\n";
    s += "Required tests:\n";
    s += "- quit_dialog_script(CloseJobKind::Import) is syntactically valid JavaScript AND still contains data-choice=cancel_and_quit. Parse for real (node --check on the emitted script, or an equivalent parser). Substring-only is a fail.\n";
    s += "- Processing script still has no Quit and cancel.\n";
    s += "- Handshake timeout / invalid first payload maps to CloseChoice::Stay. Explicit cancel_and_quit and quit_anyway unchanged.\n";
    s += "Run cargo test in apps/desktop/src-tauri until green. Capture " + scratch_path() + "/cargo-test-C.txt.\n";
    s += "Do not change apps/web. Do not add a processing cancel route.\n";
    s += "Commit message exactly: desktop: fix import quit dialog script and stay fallback\n";
    s += "Push. Return stage=开发-C, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=summary.\n";
    s
}

fn develop_d_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for 开发 slice D: F005 (joe-cheung-cae/frame-pilot#31) plus the 开发 stage close-out.\n";
    s += shared_rules();
    s += "Slice C MUST already be committed. Tests first. Drive shipped functions.\n";
    s += "Problem: app.run matches RunEvent::Exit | ExitRequested { .. } and always request_shutdown(); matches! discards ExitRequestApi so prevent_exit cannot run. Cmd+Q skips the close dialog.\n";
    s += "Implement: On ExitRequested, prevent_exit and run the same close_decision flow as CloseRequested (reuse handle_close_requested or a shared helper). request_shutdown only after Stay is declined, and after CancelThenTerminate has waited up to CANCEL_WAIT. RunEvent::Exit may still request_shutdown as a drain. Window close path must keep working. Extract a small testable helper if needed so ExitRequested is prevent_exit'd and routed through close_decision.\n";
    s += "Stay keeps the sidecar alive. Quit and cancel import POSTs cancel. Quit anyway SIGTERMs without labelling the job cancelled.\n";
    s += "Required tests: helper proves ExitRequested is prevent_exit'd and routed through close_decision; Stay does not request_shutdown; window close path still maps through the same decision. cargo test until green. Capture " + scratch_path() + "/cargo-test-D.txt.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Commit message for the product fix exactly: desktop: route app quit through the close dialog\n";
    s += "If a docs-only tracker note needs a second commit, use a docs-only message that still leaves the required product subject on the F005 commit. Push after each commit. Do not write STATUS.md.\n";
    s += "Return stage=开发, commit=latest sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=A-D summary.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort (grok-46-high) for stage 测试.\n";
    s += shared_rules();
    s += "Fix until green. Drive the shipped code. No test theater. Do not start Phase 2. Do not bump APP_VERSION.\n";
    s += "1) cargo test in apps/desktop/src-tauri (crate framepilot-desktop) TWICE. Must include the new tests from A-D. Record count. ";
    s += "Capture " + scratch_path() + "/cargo-test-1.txt and cargo-test-2.txt and copy to evidence.\n";
    s += "If rustc/cargo missing (exit 127), capture exact command+error to " + scratch_path() + "/tauri-toolchain.txt AND " + evidence_path() + "/tauri-toolchain.txt, ";
    s += "mark A-D [~] with a dated ISO-8601-with-timezone note in docs/desktop_feasibility_notes.md, keep the code, and do not claim those tests passed. Still run the non-Rust checks below.\n";
    s += "A successful cargo run that fails the new assertions is a product fail, not an environment fallback.\n";
    s += "2) npm run test:web -> " + scratch_path() + "/test-web.log (exit 0). Copy to evidence.\n";
    s += "3) npm run verify -> " + scratch_path() + "/verify.log (exit 0). Must stay rust-free. Fail if verify invokes rustc, cargo, or tauri. Use fail-if-invoked wrappers on PATH to prove this. Copy to evidence.\n";
    s += "4) Do not run job pytest unless you touched API (you should not).\n";
    s += "5) If tests/desktop/smoke.sh or npm run test:desktop:smoke exists, run it and capture " + scratch_path() + "/desktop-smoke.txt.\n";
    s += "GUI WebView of the overlay is not required if unit tests prove the import script parses and Stay is the unconfirmed fallback.\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Commit message exactly: test: verify desktop review-fix behavior\n";
    s += "Then git push -u origin HEAD. Append log+status to scratch.\n";
    s += "Return stage=测试, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=commands and results including cargo test count.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are grok-4.6 (medium effort, general-purpose) for stage 上线.\n";
    s += shared_rules();
    s += "上线 means record review-fix close-out on feature/desktop-packaging. Do not open a PR. Do not merge to main. Do not start Phase 2-5. Do not close GitHub issues.\n";
    s += "Do not write retired handoff docs. Record close-out against docs/plans/2026-08-18-desktop-packaging.md section 5.1 only if needed; do not retick Phase 1 boxes. ";
    s += "Do not untick or retick D1.01-D1.09 unless a test proved a Phase 1 box was wrongly [x] (it was not).\n";
    s += "Comment on joe-cheung-cae/frame-pilot#33 #35 #36 #34 #31 #32 with: commit SHAs, tests run, evidence. Use gh issue comment. Use owner/repo#N in the comment text. Do NOT close them.\n";
    s += "Comment on joe-cheung-cae/frame-pilot#30 with the index of SHAs and leftover risk. Do NOT close #30.\n";
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "(example 2026-08-20T16:00:00+08:00). Never date-only. Run date and format the offset with a colon.\n";
    s += "Commit message exactly: docs: record desktop review-fix close-out\n";
    s += "Then git push -u origin HEAD. Append log+status to scratch.\n";
    s += "Do not claim complete if rustc was missing and A-D were only [~]. In that case set status=blocked, next_stage=none, and still comment with what landed.\n";
    s += "Return stage=上线, commit=sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=close-out summary including comment URLs.\n";
    s
}

phase("需求拆解");
log("Starting 需求拆解 with medium-effort grok-4.6 plan agent");
let r1 = agent(breakdown_prompt(), medium_plan_opts("review-fix-breakdown"));
if !stage_ok(r1) {
    pause("no_progress", "需求拆解 failed; inspect the agent before 评审. A resume will re-pause until this journaled result changes.");
}

phase("评审");
log("Starting 评审 with medium-effort grok-4.6 plan agent");
let r2 = agent(review_prompt(), medium_plan_opts("review-fix-review"));
if !stage_ok(r2) {
    pause("no_progress", "评审 failed; inspect the agent before 归档. A resume will re-pause until this journaled result changes.");
}
if review_is_reject(r2) {
    pause("verification", "评审 rejected the breakdown; do not start 归档 until the contract is revised. A resume will re-pause until the journaled verdict changes.");
}

phase("归档");
log("Starting 归档 with low-effort grok-4.6 general-purpose agent");
let r3 = agent(archive_prompt(), archive_opts("review-fix-archive"));
if !stage_ok(r3) {
    pause("no_progress", "归档 failed; inspect the agent before 开发. A resume will re-pause until this journaled result changes.");
}

phase("开发");
log("Starting 开发 A F001+F006 terminate-on-error with high-effort grok-4.6");
let r4a = agent(develop_a_prompt(), high_opts("review-fix-dev-A"));
if !stage_ok(r4a) {
    pause("no_progress", "开发 A failed; inspect before B. A resume will re-pause until this journaled result changes.");
}
log("Starting 开发 B F002 shutdown-aware supervisor with high-effort grok-4.6");
let r4b = agent(develop_b_prompt(), high_opts("review-fix-dev-B"));
if !stage_ok(r4b) {
    pause("no_progress", "开发 B failed; inspect before C. A resume will re-pause until this journaled result changes.");
}
log("Starting 开发 C F003+F004 import overlay and Stay fallback with high-effort grok-4.6");
let r4c = agent(develop_c_prompt(), high_opts("review-fix-dev-C"));
if !stage_ok(r4c) {
    pause("no_progress", "开发 C failed; inspect before D. A resume will re-pause until this journaled result changes.");
}
log("Starting 开发 D F005 ExitRequested close dialog with high-effort grok-4.6");
let r4d = agent(develop_d_prompt(), high_opts("review-fix-dev-D"));
if !stage_ok(r4d) {
    pause("no_progress", "开发 D failed; inspect before 测试. A resume will re-pause until this journaled result changes.");
}

phase("测试");
log("Starting 测试 with high-effort grok-4.6 grok-46-high agent");
let r5 = agent(test_prompt(), high_opts("review-fix-test"));
if !stage_ok(r5) {
    pause("no_progress", "测试 failed; inspect the agent before 上线. A resume will re-pause until this journaled result changes.");
}

phase("上线");
log("Starting 上线 with medium-effort grok-4.6 general-purpose agent");
let r6 = agent(launch_prompt(), launch_opts("review-fix-launch"));
if !stage_ok(r6) {
    pause("no_progress", "上线 failed; inspect the agent. A resume will re-pause until this journaled result changes.");
}

complete(#{
    summary: "Desktop review-fix serial pipeline finished on feature/desktop-packaging",
    stages: ["需求拆解", "评审", "归档", "开发", "测试", "上线"],
    handoff: "docs/plans/2026-08-18-desktop-packaging.md",
    parent_issue: "joe-cheung-cae/frame-pilot#30",
});
