let meta = #{
    name: "phase7-j7-06",
    description: "Serial J7.06 pipeline: 需求拆解, 评审, 归档, 开发, 测试, 上线 for Phase 7 docs close-out",
    when_to_use: "Land FramePilot J7.06 (bilingual docs close-out) on feature/phase7-processing-cancel",
    phases: [
        #{ title: "需求拆解", detail: "Contract for J7.06 docs only" },
        #{ title: "评审", detail: "Adversarial review that J7.01-J7.05 are [x] before docs claim done" },
        #{ title: "归档", detail: "Confirm J7.03 J7.04 J7.05 are [x] and J7.06 is [ ]" },
        #{ title: "开发", detail: "Bilingual docs + CHANGELOG Unreleased + DoD ticks" },
        #{ title: "测试", detail: "npm run verify" },
        #{ title: "上线", detail: "Push, comment on 145/146, do not auto-close issues" },
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

fn shared_rules() {
    let s = "";
    s += "Resolve the repo with: git rev-parse --show-toplevel. Do not hardcode machine home paths.\n";
    s += "ONE TASK ONLY: J7.06 Docs close-out. GitHub #145 / #146. Plan J7.06. J7.07 stays [ ] or mark [-] with a dated note; do not implement pause.\n";
    s += "Branch must stay feature/phase7-processing-cancel. Create it from origin/main (include the Phase 7 plan docs) if missing. Do not checkout main for commits. Do not merge to main. Do not squash. Do not force-push.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, commits. Bilingual living docs when you touch docs. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not bump APP_VERSION. Do not sign. Do not run packaged NSIS/DMG. Do not work issue 144. Do not implement J7.07 pause.\n";
    s += "J7.03, J7.04, and J7.05 must already be [x]. Do not change production cancel logic except docs. Update api.md, architecture.md, v2_known_limitations.md, desktop_user_guide.md, desktop_testing.md, CHANGELOG.md, all with zh pairs. Remove processing jobs still have no cancel route. Export still 422. Pause still not implemented.\n";
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>'.\n";
    s += "GITHUB: after the development commit, git push -u origin HEAD. After the first successful push of this branch, if no open PR exists for head feature/phase7-processing-cancel against main, create ONE PR: title 'v2: processing job cancel (Phase 7)', body must say Refs #145 #146 and must not say Fixes or Close. Never open a second PR; later tasks only push.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: close out Phase 7 processing job cancel', do not redo implementation. Return ok=true with that SHA.\n";
    s += "Tick J7.06 [x] and Phase 7 DoD boxes in the SAME commit. Optionally mark J7.07 [-] with a dated not-DoD note. Do not close #145/#146 via Fixes.\n";
    s
}

fn github_tail() {
    let s = "";
    s += "Then git push -u origin HEAD.\n";
    s += "Ensure a single PR exists for feature/phase7-processing-cancel into main (create if missing, never a second PR). Refs #145 #146 only.\n";
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

fn plan_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        agent_type: "plan",
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

fn breakdown_prompt() {
    let s = "";
    s += "You are the 需求拆解 agent for FramePilot J7.06. Documentation contract only. Do not implement production behavior yet.\n";
    s += shared_rules();
    s += "Checkout feature/phase7-processing-cancel if needed.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md section 1.1 and 10.5, docs/plans/2026-09-03-phase7-processing-cancel.md for J7.06, and the live files listed here: docs/api.md, docs/architecture.md, docs/v2_known_limitations.md, docs/desktop_user_guide.md, docs/desktop_testing.md, CHANGELOG.md, and matching .zh.md files, plus the Phase 7 plan §3/§7.\n";
    s += "Write a short contract into the plan only if a hole exists; otherwise do not churn docs.\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += "Return ok=true, stage=需求拆解, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=contract summary.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are the 评审 agent for FramePilot J7.06. Adversarially review the contract against the live tree. Do not implement production code unless fixing a bilingual plan hole.\n";
    s += shared_rules();
    s += "Read the live files: docs/api.md, docs/architecture.md, docs/v2_known_limitations.md, docs/desktop_user_guide.md, docs/desktop_testing.md, CHANGELOG.md, and matching .zh.md files, plus the Phase 7 plan §3/§7.\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += "Return ok=true, stage=评审, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=review summary.\n";
    s
}

fn skeptic_prompt() {
    let s = "";
    s += "You are a read-only skeptic for J7.06. Use grep/read_file on live code. Do not edit.\n";
    s += "Confirm the task is still the right next slice and that dependencies in the plan section 3 are actually [x] in the working tree. Set real=true only with evidence you read. ok=true if J7.06 should proceed. notes=short. evidence=file:line citations.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are the 归档 agent for FramePilot J7.06. Do not implement production code.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-09-03-phase7-processing-cancel.md section 3. Confirm J7.03 J7.04 J7.05 are [x] and J7.06 is [ ]\n";
    s += "If J7.06 is already [x] AND the implementation commit exists, return ok=true and do not rewrite history.\n";
    s += "If required dependency boxes are still [ ], set ok=false and do not continue.\n";
    s += "Return ok=true, stage=归档, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=ready for 开发.\n";
    s
}

fn develop_prompt() {
    let s = "";
    s += "You are the 开发 agent for FramePilot J7.06. Tests first, then minimal implementation.\n";
    s += shared_rules();
    s += "FILES: docs/api.md, docs/architecture.md, docs/v2_known_limitations.md, docs/desktop_user_guide.md, docs/desktop_testing.md, CHANGELOG.md, and matching .zh.md files, plus the Phase 7 plan §3/§7.\n";
    s += "TESTS FIRST: No production tests to invert. Docs-only. Do not claim behavior the code does not have: read cancel_job_endpoint and sidecar.rs before writing.\n";
    s += "Run: npm run verify\n";
    s += "Commit subject exactly: docs: close out Phase 7 processing job cancel\n";
    s += "Include tests/implementation/docs ticks in that commit.\n";
    s += github_tail();
    s += "Return ok=true only if the named tests passed and the commit exists. stage=开发, commit=full sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=summary.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are the 测试 agent for FramePilot J7.06. Fail closed. Re-run tests yourself. Do not start the next J7 id.\n";
    s += shared_rules();
    s += "1) git log origin/main..HEAD --oneline must include: docs: close out Phase 7 processing job cancel\n";
    s += "2) Re-run: npm run verify\n";
    s += "3) Scope: Do not launch packaged GUI. git diff should be documentation + changelog + plan ticks, not new cancel semantics.\n";
    s += "Set passed=true only if you ran the command and it exited 0 (or for rustc-missing J7.05, passed=false). ok=true only if passed=true and scope is clean.\n";
    s += "If tests fail, fix only this task's files, keep one logical commit, re-run.\n";
    s += "Return stage=测试, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are the 上线 agent for FramePilot J7.06. Do not start the next J7 id.\n";
    s += shared_rules();
    s += "Confirm git push happened. Confirm the single PR exists (create if missing).\n";
    s += "Comment on joe-cheung-cae/frame-pilot#146 with J7.06, full SHA, test command. Do not close #145 or #146.\n";
    s += "Return ok=true, stage=上线, commit=full sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=PR URL and comment.\n";
    s
}

phase("需求拆解");
log("J7.06 需求拆解");
run_stage(breakdown_prompt(), plan_opts("j706-breakdown"), "J7.06 需求拆解 failed; inspect before 评审.");

phase("评审");
log("J7.06 评审");
run_stage(review_prompt(), plan_opts("j706-review"), "J7.06 评审 failed; inspect before 归档.");
let sk = agent(skeptic_prompt(), skeptic_opts("j706-skeptic"));
if !stage_ok(sk) {
    await_user("verification", "J7.06 skeptic agent failed. Resume to retry 评审. Do not skip to 开发.");
    sk = agent(skeptic_prompt(), skeptic_opts("j706-skeptic"));
}
if stage_ok(sk) && sk.output != () && sk.output.real == false {
    await_user("verification", "J7.06 skeptic set real=false. Resume only after the contract matches live code.");
}

phase("归档");
log("J7.06 归档");
run_stage(archive_prompt(), agent_opts("j706-archive"), "J7.06 归档 failed; inspect before 开发.");

phase("开发");
log("J7.06 开发");
run_stage(develop_prompt(), agent_opts("j706-develop"), "J7.06 开发 failed; inspect before 测试. Do not skip the GitHub push.");

phase("测试");
log("J7.06 测试");
let test_r = run_stage(test_prompt(), test_opts("j706-test"), "J7.06 测试 failed; do not 上线.");
if !declared_passed(test_r) {
    await_user("verification", "J7.06 tests did not pass. Resume to retry 测试. Do not 上线.");
}

phase("上线");
log("J7.06 上线");
let launch_r = run_stage(launch_prompt(), agent_opts("j706-launch"), "J7.06 上线 failed; inspect git push and issue comment.");
let launch_commit = "";
let launch_notes = "J7.06 workflow finished";
if launch_r != () && launch_r.output != () {
    if launch_r.output.commit != () {
        launch_commit = launch_r.output.commit;
    }
    if launch_r.output.notes != () {
        launch_notes = launch_r.output.notes;
    }
}
complete(#{
    ok: stage_ok(launch_r) && declared_ok(launch_r),
    task: "J7.06",
    commit: launch_commit,
    notes: launch_notes,
});
