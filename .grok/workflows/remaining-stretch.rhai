let meta = #{
    name: "remaining-stretch",
    description: "One Phase 9 GitHub issue per run: 需求拆解, 评审, 归档, 开发, 测试, 上线",
    when_to_use: "Land FramePilot S9.01-S9.13 on feature/remaining-stretch, one issue per launch",
    phases: [
        #{ title: "S9.00", detail: "Schedule (idempotent if already landed)" },
        #{ title: "S9.01", detail: "Export job cancel #164" },
        #{ title: "S9.02", detail: "J7.07 processing pause #161" },
        #{ title: "S9.03", detail: "AVIF still preview #163" },
        #{ title: "S9.04", detail: "RAW embedded preview #162" },
        #{ title: "S9.05", detail: "XMP sidecar export #165" },
        #{ title: "S9.06", detail: "Optional system tray #169" },
        #{ title: "S9.07", detail: "Detached preview window #166" },
        #{ title: "S9.08", detail: "Opt-in import concurrency #168" },
        #{ title: "S9.09", detail: "Change data directory #170" },
        #{ title: "S9.10", detail: "Optional check for updates #167" },
        #{ title: "S9.11", detail: "Signing-ready CI #171" },
        #{ title: "S9.12", detail: "macOS DMG GUI QA #172" },
        #{ title: "S9.13", detail: "Docs leftover repair #173" },
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

fn known_slice(id) {
    id == "s900" || id == "s901" || id == "s902" || id == "s903" || id == "s904" || id == "s905" || id == "s906" || id == "s907" || id == "s908" || id == "s909" || id == "s910" || id == "s911" || id == "s912" || id == "s913"
}

fn slice_title(id) {
    if id == "s900" { return "S9.00"; }
    if id == "s901" { return "S9.01"; }
    if id == "s902" { return "S9.02"; }
    if id == "s903" { return "S9.03"; }
    if id == "s904" { return "S9.04"; }
    if id == "s905" { return "S9.05"; }
    if id == "s906" { return "S9.06"; }
    if id == "s907" { return "S9.07"; }
    if id == "s908" { return "S9.08"; }
    if id == "s909" { return "S9.09"; }
    if id == "s910" { return "S9.10"; }
    if id == "s911" { return "S9.11"; }
    if id == "s912" { return "S9.12"; }
    "S9.13"
}

fn slice_issue(id) {
    if id == "s900" { return "160"; }
    if id == "s901" { return "164"; }
    if id == "s902" { return "161"; }
    if id == "s903" { return "163"; }
    if id == "s904" { return "162"; }
    if id == "s905" { return "165"; }
    if id == "s906" { return "169"; }
    if id == "s907" { return "166"; }
    if id == "s908" { return "168"; }
    if id == "s909" { return "170"; }
    if id == "s910" { return "167"; }
    if id == "s911" { return "171"; }
    if id == "s912" { return "172"; }
    "173"
}

fn slice_subject(id) {
    if id == "s900" { return "docs: schedule remaining stretch S9.00–S9.13"; }
    if id == "s901" { return "v2: allow cooperative cancel on export jobs"; }
    if id == "s902" { return "v2: cooperative pause for processing jobs"; }
    if id == "s903" { return "v2: import AVIF still previews"; }
    if id == "s904" { return "v2: extract RAW embedded previews"; }
    if id == "s905" { return "v2: write XMP sidecars in export directory"; }
    if id == "s906" { return "desktop: optional system tray"; }
    if id == "s907" { return "desktop: detached preview window"; }
    if id == "s908" { return "desktop: opt-in import worker concurrency"; }
    if id == "s909" { return "desktop: change data directory with path rewrite"; }
    if id == "s910" { return "desktop: optional check for updates"; }
    if id == "s911" { return "ci: sign desktop installers when secrets exist"; }
    if id == "s912" { return "docs: macOS DMG GUI lifecycle QA"; }
    "docs: close out remaining stretch S9"
}

fn slice_contract(id) {
    let s = "";
    if id == "s900" {
        s += "S9.00 schedule only. Docs + GitHub issues + this workflow. No product behavior. Idempotent if already committed.\n";
        return s;
    }
    if id == "s901" {
        s += "S9.01 Export job cancel. GitHub #164. Allow job_type export on cancel_job_endpoint. Cooperative checkpoints. Partial ZIP/folder fail-and-cleanup. Fix detail Only import jobs can be cancelled. Desktop quit can cancel an active export. Import/processing cancel tests stay green. Originals untouched.\n";
        s += "TESTS FIRST: invert export 422 in apps/api/tests/test_import_process_export_api.py. queued/running export cancel -> 202 + flag; terminal -> 200 noop; originals untouched.\n";
        s += "Do not implement S9.02-S9.13. Do not add export durable resume.\n";
        return s;
    }
    if id == "s902" {
        s += "S9.02 J7.07 pause. GitHub #161. Distinct pause_requested, not cancellation_requested. Worker exits at existing processing checkpoints without cancelled finalize and without reviewable partial groups. Resume is POST /process clear-and-rerun. Tick J7.07 [x] with that note.\n";
        s += "Do not keep half-built groups. Do not implement S9.01 or S9.03-S9.13.\n";
        return s;
    }
    if id == "s903" {
        s += "S9.03 AVIF still preview. GitHub #163. Add .avif to SUPPORTED_EXTENSIONS and STORED_IMAGE_EXTENSIONS via existing pillow-heif opener. ImportPanel accept. PyInstaller collect. Tiny AVIF generated in pytest. Not RAW.\n";
        s += "Do not implement RAW, XMP, or other S9 ids.\n";
        return s;
    }
    if id == "s904" {
        s += "S9.04 RAW embedded preview. GitHub #162. Copy original bytes. Extract embedded preview only. WebP derivatives. No thumb -> skip with explicit local message. No demosaic. No camera files in git. Document LibRaw license like libheif.\n";
        s += "Do not implement AVIF, XMP, or other S9 ids.\n";
        return s;
    }
    if id == "s905" {
        s += "S9.05 XMP sidecar export. GitHub #165. Historical #117. Optional export checkbox default off. Write .xmp only in project export directory. Never originals/ or camera originals. Map Pick/Maybe/Reject and stars. Originals byte-identical. ZIP includes sidecars when enabled.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    if id == "s906" {
        s += "S9.06 Optional system tray D3.06. GitHub #169. Progress during background jobs. No extra fs: or shell: capabilities. Tick D3.06.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    if id == "s907" {
        s += "S9.07 Detached preview window. GitHub #166. Second WebView plus shared culling selection. If WebView fails, keep in-shell preview.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    if id == "s908" {
        s += "S9.08 Opt-in import concurrency. GitHub #168. Settings 1-4 import workers, default 1. One processing job per project. No Redis/Celery.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    if id == "s909" {
        s += "S9.09 Change data directory. GitHub #170. Explicit authorize using D2.00 allowlist. Rewrite stored project paths. Never rewrite camera-card originals.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    if id == "s910" {
        s += "S9.10 Optional check for updates. GitHub #167. Menu click only. GitHub Releases. No launch-time network. Missing manifest is non-fatal. Unsigned builds still launch.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    if id == "s911" {
        s += "S9.11 Signing-ready CI. GitHub #171. Gate Authenticode/notarization in .github/workflows/desktop.yml on secrets. Unsigned fallback stays green. Update docs/desktop_signing.md (+ zh) with secret names. No certs in git.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    if id == "s912" {
        s += "S9.12 macOS DMG GUI lifecycle QA. GitHub #172. Follow docs/desktop_testing.md. If no Mac host, record skip with ISO-8601 timestamp; skip is not a pass. await_user for a Mac if needed.\n";
        s += "Do not implement other S9 ids.\n";
        return s;
    }
    s += "S9.13 Docs leftover repair. GitHub #173. Align docs/desktop_development_plan.md section 2.2. Refresh known limitations, README, CHANGELOG, implement_goals.md. Do not claim 2.2 items done unless their S9 boxes are [x]. PR body may say Fixes only after this issue.\n";
    s += "Do not implement product features in this docs issue.\n";
    s
}

fn shared_rules(id) {
    let title = slice_title(id);
    let issue = slice_issue(id);
    let subject = slice_subject(id);
    let s = "";
    s += "Resolve the repo with: git rev-parse --show-toplevel. Do not hardcode machine home paths.\n";
    s += "ONE TASK ONLY: " + title + ". GitHub umbrella #160, this issue #" + issue + ". Plan: docs/plans/2026-09-04-remaining-stretch.md (and .zh.md).\n";
    s += slice_contract(id);
    s += "Branch must stay feature/remaining-stretch. Create it from origin/main if missing. Do not checkout main for commits. Do not merge to main. Do not squash. Do not force-push.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, commits. Bilingual living docs when you touch docs. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled neural models. Do not bump APP_VERSION. Do not commit certs, camera photos, or model weights.\n";
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>'.\n";
    s += "GITHUB: after the development commit, git push -u origin HEAD. After the first successful push of this branch, if no open PR exists for head feature/remaining-stretch against main, create ONE draft PR: title 'v2: remaining stretch close-out (Phase 9)', body must say Refs #160 #" + issue + " and must not say Fixes or Close (S9.13 may add Fixes later). Never open a second PR; later tasks only push.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject '" + subject + "', do not redo implementation. Return ok=true with that SHA.\n";
    s += "Tick " + title + " [x] in docs/plans/2026-09-04-remaining-stretch.md section 3 (and the zh file) in the SAME commit as the implementation. Do not tick other S9 boxes.\n";
    s
}

fn github_tail(id) {
    let issue = slice_issue(id);
    let s = "";
    s += "Then git push -u origin HEAD.\n";
    s += "Ensure a single draft PR exists for feature/remaining-stretch into main (create if missing, never a second PR). Refs #160 #" + issue + " only. Do not say Fixes or Close unless this is S9.13.\n";
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

fn breakdown_prompt(id) {
    let title = slice_title(id);
    let s = "";
    s += "You are the 需求拆解 agent for FramePilot " + title + ". Documentation contract only. Do not implement production behavior yet.\n";
    s += shared_rules(id);
    s += "Read with tools: AGENTS.md, develop_plan.md section 1.1, docs/plans/2026-09-04-remaining-stretch.md (this id and locked decisions), and the live files named in that plan for this id.\n";
    s += "Write a short contract into the plan only if a hole exists; otherwise do not churn docs.\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += "Return ok=true, stage=需求拆解, commit=HEAD sha, handoff=docs/plans/2026-09-04-remaining-stretch.md, notes=contract summary.\n";
    s
}

fn review_prompt(id) {
    let title = slice_title(id);
    let s = "";
    s += "You are the 评审 agent for FramePilot " + title + ". Adversarially review the contract against the live tree. Do not implement production code.\n";
    s += shared_rules(id);
    s += "Fix bilingual plan holes only if the live code makes the written spec wrong. Do not tick this id [x] yet.\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += "Return ok=true, stage=评审, commit=HEAD sha, handoff=docs/plans/2026-09-04-remaining-stretch.md, notes=review summary.\n";
    s
}

fn skeptic_prompt(id) {
    let title = slice_title(id);
    let s = "";
    s += "You are a read-only skeptic for " + title + ". Use grep/read_file on live code. Do not edit.\n";
    s += "Confirm with evidence (file:line) that this id is still the right next slice per develop_plan.md section 1.1 and the remaining-stretch plan status board, and that doing it will not modify original photos.\n";
    s += "Set real=true only with evidence you read. Set ok=true if this id is still the right next slice. notes=short.\n";
    s
}

fn archive_prompt(id) {
    let title = slice_title(id);
    let s = "";
    s += "You are the 归档 agent for FramePilot " + title + ". Do not implement production code.\n";
    s += shared_rules(id);
    s += "Read docs/plans/2026-09-04-remaining-stretch.md section 3. This id must still be [ ] (or you are idempotent after a prior commit for this id). Do not tick later ids.\n";
    s += "If this id is already [x] AND the implementation commit exists, return ok=true and do not rewrite history.\n";
    s += "Do not start coding. Return ok=true, stage=归档, commit=HEAD sha, handoff=docs/plans/2026-09-04-remaining-stretch.md, notes=ready for 开发.\n";
    s
}

fn develop_prompt(id) {
    let title = slice_title(id);
    let subject = slice_subject(id);
    let s = "";
    s += "You are the 开发 agent for FramePilot " + title + ". Tests first, then minimal implementation.\n";
    s += shared_rules(id);
    s += "TESTS FIRST for product ids. Watch new tests fail for the right reason, then implement. Docs-only ids still need bilingual plan ticks.\n";
    s += "Run the targeted tests named in the plan for this id, then npm run lint:api if you touched Python, npm run test:web and npm run typecheck if you touched UI.\n";
    s += "Commit subject exactly: " + subject + "\n";
    s += "Include tests, implementation, and section 3 tick (en+zh) in that commit.\n";
    s += github_tail(id);
    s += "Return ok=true only if the named tests passed and the commit exists. stage=开发, commit=full sha, handoff=docs/plans/2026-09-04-remaining-stretch.md, notes=summary.\n";
    s
}

fn test_prompt(id) {
    let title = slice_title(id);
    let subject = slice_subject(id);
    let s = "";
    s += "You are the 测试 agent for FramePilot " + title + ". Fail closed. Re-run tests yourself. Do not start another S9 id.\n";
    s += shared_rules(id);
    s += "1) git log -1 --format='%s' must be " + subject + " (or that subject exists on the branch).\n";
    s += "2) Re-run the targeted tests for this id. For docs-only ids, confirm the bilingual plan tick and that git diff origin/main...HEAD has no original photos, certs, or model weights.\n";
    s += "3) git diff origin/main...HEAD --stat must stay inside this id's file map.\n";
    s += "Set passed=true only if you ran the checks and they succeeded. ok=true only if passed=true and scope is clean.\n";
    s += "If tests fail, fix only this id's files, keep one logical commit (amend only if HEAD is this id's commit and not yet depended on), re-run.\n";
    s += "Return stage=测试, commit=HEAD sha, handoff=docs/plans/2026-09-04-remaining-stretch.md, notes=commands and results.\n";
    s
}

fn launch_prompt(id) {
    let title = slice_title(id);
    let issue = slice_issue(id);
    let s = "";
    s += "You are the 上线 agent for FramePilot " + title + ". Do not start another S9 id.\n";
    s += shared_rules(id);
    s += "Confirm git status clean except untracked noise. Confirm push happened. Confirm the single draft PR exists (create if missing).\n";
    s += "Comment on joe-cheung-cae/frame-pilot#" + issue + " with " + title + ", full SHA, and test commands. Do not close #160. Do not close this issue unless this is S9.13 and verify is green. Do not comment that a later S9 id is done.\n";
    s += "Return ok=true, stage=上线, commit=full sha, handoff=docs/plans/2026-09-04-remaining-stretch.md, notes=PR URL and comment.\n";
    s
}

let slice_arg = if args == () { () } else { args.slice };
if slice_arg == () || slice_arg == "" {
    pause("verification", "Pass args.slice as s901 .. s913 (one GitHub issue per run). s900 is the schedule commit.");
}
let slice = slice_arg;
if type_of(slice) != "string" {
    pause("verification", "args.slice must be a string like s901.");
}
slice.trim();
if !known_slice(slice) {
    pause("verification", "Unknown args.slice. Use s900 .. s913. One issue per run; do not pass all.");
}

let title = slice_title(slice);
phase(title);
log("Phase 9 " + title + " GitHub #" + slice_issue(slice));

run_stage(breakdown_prompt(slice), plan_opts(slice + "-breakdown"), title + " 需求拆解 failed; inspect before 评审.");
run_stage(review_prompt(slice), plan_opts(slice + "-review"), title + " 评审 failed; inspect before 归档.");

let sk = agent(skeptic_prompt(slice), skeptic_opts(slice + "-skeptic"));
if !stage_ok(sk) {
    await_user("verification", title + " skeptic agent failed. Resume to retry 评审. Do not skip to 开发.");
    sk = agent(skeptic_prompt(slice), skeptic_opts(slice + "-skeptic"));
}
if stage_ok(sk) && sk.output != () && sk.output.real == false {
    await_user("verification", title + " skeptic set real=false. Resume only after the contract matches live code.");
}

run_stage(archive_prompt(slice), agent_opts(slice + "-archive"), title + " 归档 failed; inspect before 开发.");
run_stage(develop_prompt(slice), agent_opts(slice + "-develop"), title + " 开发 failed; inspect before 测试. Do not skip the GitHub push.");

let test_r = run_stage(test_prompt(slice), test_opts(slice + "-test"), title + " 测试 failed; do not 上线.");
if !declared_passed(test_r) {
    await_user("verification", title + " tests did not pass. Resume to retry 测试. Do not 上线.");
}

let launch_r = run_stage(launch_prompt(slice), agent_opts(slice + "-launch"), title + " 上线 failed; inspect git push and issue comment.");
complete(#{
    ok: stage_ok(launch_r) && declared_ok(launch_r),
    task: title,
    issue: slice_issue(slice),
    commit: if launch_r != () && launch_r.output != () { launch_r.output.commit } else { "" },
    notes: if launch_r != () && launch_r.output != () { launch_r.output.notes } else { title + " workflow finished" },
});
