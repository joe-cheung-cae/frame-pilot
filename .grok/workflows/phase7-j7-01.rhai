let meta = #{
    name: "phase7-j7-01",
    description: "Serial J7.01 pipeline: 需求拆解, 评审, 归档, 开发, 测试, 上线 for processing-job cancel route",
    when_to_use: "Land FramePilot J7.01 (cancel route accepts processing jobs) on feature/phase7-processing-cancel",
    phases: [
        #{ title: "需求拆解", detail: "Contract for J7.01 cancel route only" },
        #{ title: "评审", detail: "Adversarial review against live cancel_job_endpoint" },
        #{ title: "归档", detail: "Confirm J7.01 is [ ] and dependencies are ready" },
        #{ title: "开发", detail: "Tests-first cancel route for processing jobs" },
        #{ title: "测试", detail: "pytest cancel tests; import cancel still green" },
        #{ title: "上线", detail: "Push, tick tracker, comment on issue 146" },
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
    s += "ONE TASK ONLY: J7.01 Cancel route accepts processing jobs. GitHub #145 umbrella, #146 implement. Plan: docs/plans/2026-09-03-phase7-processing-cancel.md (and .zh.md).\n";
    s += "Branch must stay feature/phase7-processing-cancel. Create it from origin/main (include the Phase 7 plan docs) if missing. Do not checkout main for commits. Do not merge to main. Do not squash. Do not force-push.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, commits. Bilingual living docs when you touch docs. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not implement J7.02-J7.07. Do not change ProcessingPanel or sidecar.rs. Do not bump APP_VERSION. Do not sign. Do not run packaged NSIS/DMG. Do not work issue 144.\n";
    s += "Do not send processing jobs through request_import_job_cancellation. Put request_processing_job_cancellation in apps/api/app/services/processing.py.\n";
    s += "Export jobs stay 422. Import cancel tests must stay green.\n";
    s += "Interrupted processing cancel in J7.01 finalizes cancelled immediately AND reset_project_after_processing_failure. queued/running only persist cancellation_requested and return 202; do not change status yet (J7.02 stops the worker).\n";
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>'.\n";
    s += "GITHUB: after the development commit, git push -u origin HEAD. After the first successful push of this branch, if no open PR exists for head feature/phase7-processing-cancel against main, create ONE PR: title 'v2: processing job cancel (Phase 7)', body must say Refs #145 #146 and must not say Fixes or Close. Never open a second PR; later tasks only push.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'v2: allow cooperative cancel on processing jobs', do not redo implementation. Return ok=true with that SHA.\n";
    s += "Tick J7.01 [x] in docs/plans/2026-09-03-phase7-processing-cancel.md section 3 (and the zh file) in the SAME commit as the implementation. Do not tick J7.02-J7.07.\n";
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
    s += "You are the 需求拆解 agent for FramePilot J7.01. Documentation contract only. Do not implement production cancel behavior yet.\n";
    s += shared_rules();
    s += "Checkout feature/phase7-processing-cancel if needed.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md section 1.1 and 10.5, docs/plans/2026-09-03-phase7-processing-cancel.md J7.01 and locked decisions, ";
    s += "apps/api/app/api/routes.py cancel_job_endpoint, apps/api/app/services/importing.py request_import_job_cancellation, ";
    s += "apps/api/app/services/processing.py reset_project_after_processing_failure, apps/api/tests/test_job_reliability.py test_processing_job_has_no_cancel_route_and_startup_sweep_resets_photos, ";
    s += "apps/api/tests/test_import_process_export_api.py cancel tests.\n";
    s += "Write a short J7.01 contract into the plan only if a hole exists; otherwise do not churn docs. List files, tests-first cases, HTTP mapping, non-goals (no worker checkpoints, no UI, no desktop).\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += "Return ok=true, stage=需求拆解, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=contract summary.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are the 评审 agent for FramePilot J7.01. Adversarially review the J7.01 contract against the live tree. Do not implement production code.\n";
    s += shared_rules();
    s += "Read cancel_job_endpoint, request_import_job_cancellation, reset_project_after_processing_failure, and the 422 test. Confirm: processing allowed; export still 422; interrupted processing finalizes cancelled plus group reset; queued/running only set the flag; originals untouched; no /retry expansion.\n";
    s += "Fix bilingual plan holes only if the live code makes the written J7.01 spec wrong. Do not tick J7.01 [x] yet.\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += "Return ok=true, stage=评审, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=review summary.\n";
    s
}

fn skeptic_prompt() {
    let s = "";
    s += "You are a read-only skeptic for J7.01. Use grep/read_file on live code. Do not edit.\n";
    s += "Confirm these claims with evidence (file:line): today cancel_job_endpoint returns 422 for job_type != import; ProcessingJob has cancellation_requested; reset_project_after_processing_failure clears groups; export jobs exist as a type that must stay 422.\n";
    s += "Set real=true only with evidence you read. Set ok=true if J7.01 is still the right next slice. notes=short.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are the 归档 agent for FramePilot J7.01. Do not implement production code.\n";
    s += shared_rules();
    s += "Read docs/plans/2026-09-03-phase7-processing-cancel.md section 3. J7.01 must still be [ ] (or you are idempotent after a prior J7.01 commit). J7.02+ must not be [x] yet unless already on the branch from a later run.\n";
    s += "If J7.01 is already [x] AND the implementation commit exists, return ok=true and do not rewrite history.\n";
    s += "Do not start coding. Return ok=true, stage=归档, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=ready for 开发.\n";
    s
}

fn develop_prompt() {
    let s = "";
    s += "You are the 开发 agent for FramePilot J7.01. Tests first, then minimal implementation.\n";
    s += shared_rules();
    s += "TESTS FIRST. Invert test_processing_job_has_no_cancel_route_and_startup_sweep_resets_photos: processing cancel must no longer 422. Keep reclaim-off startup sweep coverage for processing jobs WITHOUT a cancel flag (rename that test if needed). Add tests: queued/running processing cancel -> 202 and cancellation_requested true, originals untouched; terminal processing cancel -> 200 noop; export cancel still 422; interrupted processing cancel -> 200 cancelled, groups cleared, photos imported. Existing import cancel tests must pass.\n";
    s += "Watch the new tests fail for the right reason, then implement: cancel_job_endpoint allows job_type processing; request_processing_job_cancellation in processing.py; do not change process_project checkpoints (J7.02).\n";
    s += "Run: .venv/bin/pytest apps/api/tests/test_job_reliability.py apps/api/tests/test_import_process_export_api.py -q -k cancel\n";
    s += "Also run npm run lint:api if you touched Python.\n";
    s += "Commit subject exactly: v2: allow cooperative cancel on processing jobs\n";
    s += "Include tests, implementation, and §3 J7.01 tick (en+zh) in that commit.\n";
    s += github_tail();
    s += "Return ok=true only if tests named above passed and the commit exists. stage=开发, commit=full sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=summary.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are the 测试 agent for FramePilot J7.01. Fail closed. Re-run tests yourself. Do not start J7.02.\n";
    s += shared_rules();
    s += "1) git log -1 --format='%s' must be v2: allow cooperative cancel on processing jobs (or that subject exists on the branch).\n";
    s += "2) Re-run .venv/bin/pytest apps/api/tests/test_job_reliability.py apps/api/tests/test_import_process_export_api.py -q -k cancel\n";
    s += "3) git diff origin/main...HEAD --stat: no ProcessingPanel, no sidecar.rs, no desktop quit dialog changes.\n";
    s += "4) Read cancel_job_endpoint: processing allowed, export 422.\n";
    s += "Set passed=true only if you ran the pytest command and it exited 0. ok=true only if passed=true and scope is clean.\n";
    s += "If tests fail, fix only J7.01 files, keep one logical commit (amend only if HEAD is the J7.01 commit and not yet depended on), re-run.\n";
    s += "Return stage=测试, commit=HEAD sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are the 上线 agent for FramePilot J7.01. Do not start J7.02.\n";
    s += shared_rules();
    s += "Confirm git status clean except untracked noise. Confirm push happened. Confirm the single PR exists (create if missing).\n";
    s += "Comment on joe-cheung-cae/frame-pilot#146 with J7.01, full SHA, pytest command. Do not close #145 or #146. Do not comment that J7.02 is done.\n";
    s += "Return ok=true, stage=上线, commit=full sha, handoff=docs/plans/2026-09-03-phase7-processing-cancel.md, notes=PR URL and comment.\n";
    s
}

phase("需求拆解");
log("J7.01 需求拆解");
run_stage(breakdown_prompt(), plan_opts("j701-breakdown"), "J7.01 需求拆解 failed; inspect before 评审.");

phase("评审");
log("J7.01 评审");
run_stage(review_prompt(), plan_opts("j701-review"), "J7.01 评审 failed; inspect before 归档.");
let sk = agent(skeptic_prompt(), skeptic_opts("j701-skeptic"));
if !stage_ok(sk) {
    await_user("verification", "J7.01 skeptic agent failed. Resume to retry 评审. Do not skip to 开发.");
    sk = agent(skeptic_prompt(), skeptic_opts("j701-skeptic"));
}
if stage_ok(sk) && sk.output != () && sk.output.real == false {
    await_user("verification", "J7.01 skeptic set real=false. Resume only after the contract matches live code.");
}

phase("归档");
log("J7.01 归档");
run_stage(archive_prompt(), agent_opts("j701-archive"), "J7.01 归档 failed; inspect before 开发.");

phase("开发");
log("J7.01 开发");
run_stage(develop_prompt(), agent_opts("j701-develop"), "J7.01 开发 failed; inspect before 测试. Do not skip the GitHub push.");

phase("测试");
log("J7.01 测试");
let test_r = run_stage(test_prompt(), test_opts("j701-test"), "J7.01 测试 failed; do not 上线.");
if !declared_passed(test_r) {
    await_user("verification", "J7.01 tests did not pass. Resume to retry 测试. Do not 上线.");
}

phase("上线");
log("J7.01 上线");
let launch_r = run_stage(launch_prompt(), agent_opts("j701-launch"), "J7.01 上线 failed; inspect git push and issue comment.");
complete(#{
    ok: stage_ok(launch_r) && declared_ok(launch_r),
    task: "J7.01",
    commit: if launch_r != () && launch_r.output != () { launch_r.output.commit } else { "" },
    notes: if launch_r != () && launch_r.output != () { launch_r.output.notes } else { "J7.01 workflow finished" },
});
