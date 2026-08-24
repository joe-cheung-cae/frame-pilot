let meta = #{
    name: "phase2-code-review-fix",
    description: "Fix Phase 2 folder-import duplication, then review-fix-review until ready to merge",
    when_to_use: "Historical Phase 2 code-review loop (completed). Living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1; docs/handoff is retired",
    phases: [
        #{ title: "Fix", detail: "Tests-first fix for Issue 1 and Issue 2" },
        #{ title: "Test", detail: "Run shipped API and web import tests" },
        #{ title: "Review", detail: "Adversarial review of live Phase 2 HEAD" },
        #{ title: "Verify", detail: "Skeptic per finding; fail closed" },
        #{ title: "Repair", detail: "Fix remaining gating bugs and retest" },
        #{ title: "Close-out", detail: "Mark ready to merge when gating is zero" },
    ],
};

fn max_rounds() { 3 }
fn max_verify() { 10 }
fn stall_limit() { 2 }
fn repo_path() { "/Users/chao/workspace/repo/frame-pilot" }
fn branch_name() { "feature/desktop-phase2" }
fn base_ref() { "origin/main" }
fn scratch_path() { "/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-5f03152473a1/implementer" }
fn cache_path() { "/Users/chao/.cache/framepilot-desktop-phase2" }

fn findings_schema() {
    #{
        "type": "object",
        "required": ["findings"],
        "properties": #{
            "findings": #{
                "type": "array",
                "maxItems": 8,
                "items": #{
                    "type": "object",
                    "required": ["file", "line", "severity", "title", "issue", "suggestion", "evidence"],
                    "properties": #{
                        "file": #{ "type": "string" },
                        "line": #{ "type": "integer" },
                        "severity": #{ "type": "string", "enum": ["bug", "suggestion", "nit"] },
                        "title": #{ "type": "string" },
                        "issue": #{ "type": "string" },
                        "suggestion": #{ "type": "string" },
                        "evidence": #{ "type": "string" },
                    },
                },
            },
        },
    }
}

fn verdict_schema() {
    #{
        "type": "object",
        "required": ["real", "severity", "reason", "evidence"],
        "properties": #{
            "real": #{ "type": "boolean" },
            "severity": #{ "type": "string", "enum": ["bug", "suggestion", "nit"] },
            "reason": #{ "type": "string" },
            "evidence": #{ "type": "string" },
        },
    }
}

fn stage_schema() {
    #{
        "type": "object",
        "required": ["ok", "stage", "notes"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "stage": #{ "type": "string" },
            "commit": #{ "type": "string" },
            "handoff": #{ "type": "string" },
            "notes": #{ "type": "string" },
            "bugs": #{ "type": "integer" },
            "ready": #{ "type": "boolean" },
        },
    }
}

fn as_str(x) {
    if x == () {
        ""
    } else if type_of(x) == "string" {
        x
    } else {
        x.to_string()
    }
}

fn finding_key(f) {
    as_str(f.file) + ":" + as_str(f.line) + ":" + as_str(f.title)
}

fn gating_key(f) {
    as_str(f.severity) + "|" + as_str(f.file) + "|" + as_str(f.title)
}

fn is_gating(sev) {
    sev == "bug"
}

fn path_in_scope(p) {
    if p == () { return false; }
    if type_of(p) != "string" { return false; }
    if p == "" { return false; }
    let head5 = p.sub_string(0, 5);
    let head6 = p.sub_string(0, 6);
    let head8 = p.sub_string(0, 8);
    let head10 = p.sub_string(0, 10);
    head5 == "apps/" || head6 == "tests/" || head8 == "scripts/" || head10 == "docs/plans"
}

fn append_sev(src, sev, dest, cap) {
    let i = 0;
    while i < src.len() {
        if dest.len() >= cap { return dest; }
        let f = src[i];
        if f != () && as_str(f.severity) == sev { dest.push(f); }
        i += 1;
    }
    dest
}

fn count_sev(src, sev) {
    let n = 0;
    let i = 0;
    while i < src.len() {
        if src[i] != () && as_str(src[i].severity) == sev { n += 1; }
        i += 1;
    }
    n
}

fn shared_rules() {
    let s = "";
    s += "docs/handoff is retired. Do not create, write, or restore any docs/handoff/* file (including STATUS.md). The living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Phase 0-2 are already on main; remaining work is Phase 3-5. Do not retick completed Phase 0-2 boxes. Do not write docs/handoff/STATUS.md.\n";
    s += "Repo: " + repo_path() + "\n";
    s += "Resolve repo with git rev-parse --show-toplevel. Stay on branch " + branch_name() + ".\n";
    s += "Scratch: mkdir -p " + scratch_path() + " " + cache_path() + " && chmod 700 both. Never shared /tmp.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Do not checkout main. Do not merge to main. Do not squash. Do not force-push.\n";
    s += "Use tools. Read named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, docs, commits. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not start Phase 3-5. Do not bump APP_VERSION.\n";
    s += "Do not set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME, /, or a drive root.\n";
    s += "Do not migrate apps/web off Next.js. Do not add output: export.\n";
    s += "Do not remove the two ImportPanel file inputs when isDesktopShell is false.\n";
    s += "Do not weaken test_create_project_rejects_root_outside_allowlist.\n";
    s += "npm run verify must not install or require rustc, cargo, or Tauri.\n";
    s += "Do not add Co-authored-by Cursor trailers.\n";
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to Joe Cheung <zhangchao.simzc@outlook.com>.\n";
    s += "After every finished write stage: git add only intended files, commit, git push -u origin HEAD.\n";
    s += "If nothing is staged, do not make an empty commit.\n";
    s += "If push fails, capture the exact error to " + scratch_path() + "/git-push.txt, retry once, continue product work.\n";
    s += "Append SHA, subject, push result, PR URL to " + cache_path() + "/git-github.txt after every push.\n";
    s += "Existing PR is https://github.com/joe-cheung-cae/frame-pilot/pull/38. Never open a second PR.\n";
    s += "Tests must drive shipped functions. No test theater: do not hard-code expected values that skip the unit under test, do not re-implement the oracle, do not mock the function being asserted.\n";
    s
}

fn github_tail() {
    let s = "";
    s += "Then git push -u origin HEAD.\n";
    s += "Append SHA/subject/push/PR to " + cache_path() + "/git-github.txt.\n";
    s
}

fn code_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        agent_type: "grok-46-high",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn docs_opts(label) {
    #{
        label: label,
        capability_mode: "all",
        model: "grok-4.6",
        agent_type: "general-purpose",
        isolation_worktree: false,
        output_schema: stage_schema(),
    }
}

fn review_opts(label) {
    #{
        prompt: "",
        label: label,
        capability_mode: "read-only",
        output_schema: findings_schema(),
    }
}

fn verify_opts(label) {
    #{
        prompt: "",
        label: label,
        capability_mode: "read-only",
        output_schema: verdict_schema(),
    }
}

fn stage_ok(r) {
    r != () && r.success
}

fn fix_known_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort for stage Fix of documented Phase 2 code-review issues.\n";
    s += shared_rules();
    s += "Read with tools before editing: docs/plans/2026-08-18-desktop-packaging.md, apps/web/src/lib/api.ts (isLastPathImportSlice, importPhotosFromPaths, importPhotosFromPathsBatch), ";
    s += "apps/web/src/lib/importWorkflow.test.ts (the small-folder finalize test around line 347), ";
    s += "apps/api/app/api/routes.py import_photos_from_paths_endpoint, apps/api/app/schemas/api.py PathImportRequest, ";
    s += "apps/api/app/services/importing.py expand_import_paths register_import_file _existing_photo_for_content_hash _photo_derivatives_exist, ";
    s += "apps/api/tests/test_import_from_paths.py, apps/api/tests/test_path_import_process_export_workflow.py.\n";
    s += "IDEMPOTENT: if HEAD already implements empty-path finalize-only follow-up AND tests prove a 2-JPEG folder stays at 2 originals, do not redo. Return ok=true with the existing SHA.\n";
    s += "LOCKED FIX (Issue 1 bug + Issue 2 test):\n";
    s += "Desktop Choose-a-folder / drop-a-folder calls importPhotosFromPaths with a directory. isLastPathImportSlice is false for directories. First POST uses finalize:false. When the folder has <=100 images, remaining_paths is []. The client currently re-POSTs the SAME folder with finalize:true. The API re-expands and register_import_file copies again as name-1.jpg because in-progress photos are not treated as duplicates until derivatives exist.\n";
    s += "Implement protocol (a): do NOT re-POST the directory. After remaining_paths is empty and the slice was not finalized, POST finalize:true with job_id, expected_total, and paths:[]. The API must accept empty paths only on a finalize-only follow-up that has job_id.\n";
    s += "Client apps/web/src/lib/api.ts importPhotosFromPaths: when remainingPaths.length===0 && !isLastSlice, call importPhotosFromPathsBatch(projectId, [], { jobId, expectedTotal, finalize: true }). Keep throwing if the INITIAL paths array is empty. Keep looping leftover remaining_paths for 101+ file folders (those leftover paths are files; last slice still finalize:true).\n";
    s += "API import_photos_from_paths_endpoint: if paths is empty, require finalize==true AND job_id; skip expand_import_paths; do not register files; start derivative generation for processing photos on that job/project (same pending_derivative_ids path as today). Empty paths without job_id, or empty paths with finalize false, stay 422. Keep test_import_from_paths_rejects_relative_and_empty green.\n";
    s += "Record source_root_path when the request has a single directory path even if finalize is false (the follow-up has no folder path). Existing finalize:true single-dir behavior must remain.\n";
    s += "Optional narrow defense: in register_import_file, treat an existing same-hash same-filename photo as a hit when it is still processing_state==processing (in addition to when derivatives exist). Do not block failed-import retry. Do not mutate source files. Copies stay under project originals/.\n";
    s += "TESTS FIRST, then implementation. Drive shipped code.\n";
    s += "1) Update apps/web/src/lib/importWorkflow.test.ts test 'importPhotosFromPaths finalizes a small folder after remaining_paths is empty': assert two requests, first paths:[folder] finalize false, SECOND paths:[] finalize true with job_id and expected_total. That test must FAIL on current HEAD, then PASS after the client change. Do not keep asserting paths:[folder] on the second call.\n";
    s += "2) Add pytest in apps/api/tests/test_import_from_paths.py that runs the CLIENT HTTP sequence against TestClient: folder with two different JPEGs (hero.jpg and alt.jpg, different colors). POST finalize false with the folder path (monkeypatch run_import_derivative_job to no-op so derivatives are missing, matching the live bug). Assert remaining_paths==[] and two imported names. Then POST paths:[] job_id expected_total=2 finalize true. Assert HTTP 201, GET project total_images==2, originals/ names exactly hero.jpg and alt.jpg (no hero-1.jpg/alt-1.jpg), Photo row count==2, source files unchanged (size/mtime_ns/sha256). Also assert source_root_path is the folder. This test must FAIL on current API (empty paths 422 or duplicates if folder is re-posted).\n";
    s += "3) Keep the 250-file three-request test green. Keep D2.08 test_path_import_process_export_workflow.py green (single finalize true request).\n";
    s += "Run: .venv/bin/pytest apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_from_paths_immutability.py apps/api/tests/test_path_import_process_export_workflow.py -q\n";
    s += "Run: npm --prefix apps/web exec -- node --experimental-strip-types --test src/lib/importWorkflow.test.ts from apps/web, or the repo equivalent that already collects that file. Capture logs under " + scratch_path() + ".\n";
    s += "Commit message exactly: fix: stop duplicating photos on small folder path import\n";
    s += "If the workflow file .grok/workflows/phase2-code-review-fix.rhai is untracked, include it in this commit or a follow-up docs commit; product fix subject stays as above.\n";
    s += github_tail();
    s += "Do not update docs/handoff/*; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not write STATUS.md. Do not retick completed Phase 0-2 boxes.\n";
    s += "Return ok=true, stage=Fix, commit=full sha, handoff=docs/plans/2026-08-18-desktop-packaging.md, notes=what changed and test commands.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are grok-4.6 high-effort for stage Test after the folder-import fix.\n";
    s += shared_rules();
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md. Product/test files in the slice remain writable; docs/handoff is not.\n";
    s += "Fix until green. Drive shipped code. No test theater.\n";
    s += "1) .venv/bin/pytest apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_from_paths_immutability.py apps/api/tests/test_path_import_process_export_workflow.py apps/api/tests/test_batched_import_api.py -q\n";
    s += "Capture " + scratch_path() + "/pytest-import.txt . Must include the new small-folder finalize-only test and it must PASS.\n";
    s += "2) npm --prefix apps/web run test:unit . Capture " + scratch_path() + "/test-web-unit.log . The small-folder importPhotosFromPaths test must assert second request paths:[].\n";
    s += "3) If you touched Python/TS production files this stage, also run .venv/bin/ruff check apps/api and npm --prefix apps/web run typecheck.\n";
    s += "4) Optionally npm run verify if time allows; it must stay rust-free.\n";
    s += "Prove the bug is gone: a 2-JPEG folder client sequence ends with total_images==2 and originals named after sources. If that assertion is not in a committed test, add it and fail this stage.\n";
    s += "Do not write STATUS.md; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1.\n";
    s += "Commit message exactly: test: verify small folder path import is not duplicated\n";
    s += "If the only pending change would have been STATUS.md, skip the empty commit. Living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Do not commit scratch logs.\n";
    s += github_tail();
    s += "Return ok=true, stage=Test, commit=sha, notes=commands and results.\n";
    s
}

fn reviewer_rules() {
    let s = "";
    s += "You are a meticulous code reviewer. Check correctness first, style second.\n";
    s += shared_rules();
    s += "THIS STAGE capability_mode=read-only. Do not edit files. Do not commit. Do not push.\n";
    s += "Use read_file, grep, list_dir, and git diff/log/show. Do not answer from memory.\n";
    s += "Commands: cd " + repo_path() + " && git rev-parse --abbrev-ref HEAD && git rev-parse HEAD && git merge-base " + base_ref() + " HEAD && git -c core.quotepath=false diff " + base_ref() + "...HEAD -- <your files>.\n";
    s += "Read live source, not only the diff. An empty findings list is valid ONLY after you have read the code.\n";
    s += "Do not invent issues. Do not inflate severity. Missing Phase 3-5 work is not a defect.\n";
    s += "The previously reported folder-duplication bug is NOT a finding if live code posts paths:[] on the finalize follow-up AND tests assert 2 JPEGs stay 2 copies. If the old bug is still present, report it as severity bug.\n";
    s += "Severity bug = correctness/safety break on HEAD (duplication, original mutation, path escape, lost photos, false-green test of a live bug).\n";
    s += "suggestion = should-fix quality. nit = optional.\n";
    s += "Gating for merge is bugs only. Every finding must cite a real file path and RIGHT-side line you inspected.\n";
    s += "evidence must quote what you read. Return at most 8 findings. Prefer fewer confirmed defects.\n";
    s
}

fn review_job(label, focus, files) {
    let p = "";
    p += reviewer_rules();
    p += "Mode: branch. Target: " + branch_name() + " vs " + base_ref() + ".\n";
    p += "Dimension: " + focus + "\n";
    p += "Inspect these files (skip if a path is absent):\n";
    p += files;
    p += "\nReport JSON findings with file, line, severity (bug|suggestion|nit), title, issue, suggestion, evidence.\n";
    let job = review_opts(label);
    job.prompt = p;
    job
}

fn handoff_prompt(round, confirmed_json, bugs, suggestions, nits) {
    let s = "";
    s += "You are grok-4.6 for stage Handoff of review round " + round.to_string() + ".\n";
    s += shared_rules();
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Do not patch production code.\n";
    s += "Confirmed findings JSON (already verified; do not add extras):\n";
    s += confirmed_json;
    s += "\nCounts: bugs=" + bugs.to_string() + " suggestions=" + suggestions.to_string() + " nits=" + nits.to_string() + ".\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "If bugs=0, say so explicitly and that Phase 2 is merge-gating clean for this round.\n";
    s += "Do not write STATUS.md; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1.\n";
    s += "Commit message exactly: docs: record Phase 2 code-review round-" + round.to_string() + "\n";
    s += github_tail();
    s += "Return ok, stage=Handoff, commit=sha, notes=summary, bugs=count.\n";
    s
}

fn repair_prompt(round, confirmed_json) {
    let s = "";
    s += "You are grok-4.6 high-effort for Repair of round " + round.to_string() + ".\n";
    s += shared_rules();
    s += "Confirmed gating (bug) findings JSON:\n";
    s += confirmed_json;
    s += "\nFix every severity=bug item. Tests first. Drive shipped functions. No test theater.\n";
    s += "Stay inside Phase 2: path import, desktop FS, originals safety, tests. Do not start Phase 3-5.\n";
    s += "Run the relevant pytest and web unit tests after the fix. Capture " + scratch_path() + "/repair-round-" + round.to_string() + ".txt\n";
    s += "Do not write STATUS.md; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. Commit with a conventional English subject describing the fix. Push.\n";
    s += "Return ok, stage=Repair, commit=sha, notes=what changed and tests.\n";
    s
}

fn closeout_prompt(outcome, confirmed_json, bugs) {
    let s = "";
    s += "You are grok-4.6 for Close-out of the Phase 2 code-review loop.\n";
    s += shared_rules();
    s += "Outcome from orchestrator: " + outcome + "\n";
    s += "bugs=" + bugs.to_string() + "\n";
    s += "Confirmed JSON:\n";
    s += confirmed_json;
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Do not merge to main. Do not squash. You MAY comment on PR 38 with gh pr comment. If outcome is clean, you MAY run gh pr ready 38 if it is still draft (it may already be ready).\n";
    s += "Do not write docs/handoff/*. Use docs/plans/2026-08-18-desktop-packaging.md section 5.1 as the living contract. Do not recreate STATUS.md.\n";
    s += "Do not recreate phase2-code-review-findings.md. ";
    s += "Do not write STATUS.md. Record ready-to-merge in session notes; living tracker is docs/plans/2026-08-18-desktop-packaging.md section 5.1. ";
    s += "Comment on PR 38 that Phase 2 is ready to merge after the folder-import duplication fix; do not merge.\n";
    s += "If outcome is not clean: record blocked in session notes with remaining bugs. Do NOT claim ready to merge. Do not write STATUS.md.\n";
    s += "Commit message exactly: docs: mark desktop Phase 2 ready to merge\n";
    s += "If blocked, commit message exactly: docs: record Phase 2 code-review loop blocked\n";
    s += github_tail();
    s += "Return ok, stage=Close-out, ready=true only if outcome is clean, notes=summary including PR URL.\n";
    s
}

fn collect_raw(results) {
    let raw = [];
    let seen = #{};
    let r_i = 0;
    while r_i < results.len() {
        let r = results[r_i];
        if r != () && r.success && r.output != () && r.output.findings != () {
            let fs = r.output.findings;
            let f_i = 0;
            while f_i < fs.len() {
                let f = fs[f_i];
                if f != () && path_in_scope(as_str(f.file)) && as_str(f.issue) != "" && as_str(f.evidence) != "" {
                    let k = finding_key(f);
                    if seen[k] == () {
                        seen[k] = true;
                        raw.push(f);
                    }
                } else {
                    log("Dropped out-of-scope or incomplete finding");
                }
                f_i += 1;
            }
        }
        r_i += 1;
    }
    raw
}

fn gating_fingerprint(confirmed) {
    let keys = "";
    let i = 0;
    while i < confirmed.len() {
        let f = confirmed[i];
        if f != () && is_gating(as_str(f.severity)) {
            keys += gating_key(f);
            keys += "\n";
        }
        i += 1;
    }
    fingerprint(keys)
}

let requested_rounds = max_rounds();
if args != () && args.max_rounds != () {
    requested_rounds = args.max_rounds;
}
if requested_rounds < 1 {
    pause("verification", "Pass args.max_rounds >= 1");
}

phase("Fix");
log("Fixing documented folder-import duplication (Issue 1 and Issue 2)");
let fix = agent(fix_known_prompt(), code_opts("phase2-fix-known"));
if !stage_ok(fix) {
    pause("no_progress", "Fix of documented findings failed. Inspect before Test. A resume will re-pause until this journaled result changes.");
}

phase("Test");
log("Running shipped import tests for the folder-import fix");
let tested = agent(test_prompt(), code_opts("phase2-test-import"));
if !stage_ok(tested) {
    pause("no_progress", "Test stage failed. Inspect before Review. A resume will re-pause until this journaled result changes.");
}

let round = 1;
let last_fp = "";
let stall = 0;
let outcome = "running";
let last_confirmed = [];
let last_bugs = 0;
let last_suggestions = 0;
let last_nits = 0;

while round <= requested_rounds && outcome == "running" {
    phase("Review");
    log("Review round " + round.to_string() + " of live " + branch_name() + " HEAD");

    let import_files = "";
    import_files += "- apps/web/src/lib/api.ts importPhotosFromPaths isLastPathImportSlice importPhotosFromPathsBatch\n";
    import_files += "- apps/web/src/lib/importWorkflow.test.ts\n";
    import_files += "- apps/web/src/components/ImportPanel.tsx onPickFolder drop folder\n";
    import_files += "- apps/api/app/api/routes.py import_photos_from_paths_endpoint\n";
    import_files += "- apps/api/app/services/importing.py register_import_file expand_import_paths\n";
    import_files += "- apps/api/tests/test_import_from_paths.py\n";
    import_files += "Re-check Issue 1: small folder must not duplicate. Re-check Issue 2: mock test must not require re-POSTing the folder.\n";

    let safety_files = "";
    safety_files += "- apps/api/app/services/importing.py apps/api/app/core/project_roots.py apps/api/app/services/projects.py\n";
    safety_files += "- apps/api/tests/test_import_from_paths_immutability.py\n";
    safety_files += "- apps/desktop/src-tauri/capabilities/default.json apps/desktop/src-tauri/tauri.conf.json\n";
    safety_files += "Originals never mutated/deleted. No fs:/shell: capabilities. FRAMEPILOT_DESKTOP=1 for desktop routes. No $HOME allowlist.\n";

    let test_files = "";
    test_files += "- apps/web/src/lib/importWorkflow.test.ts apps/web/src/lib/api.ts\n";
    test_files += "- apps/api/tests/test_import_from_paths.py apps/api/tests/test_path_import_process_export_workflow.py\n";
    test_files += "False-green risk: mocked fetch that encodes a buggy protocol; D2.08 single finalize:true never hitting the client loop.\n";

    let jobs = [];
    jobs.push(review_job("review:import-protocol", "Path-import finalize protocol and small-folder duplication", import_files));
    jobs.push(review_job("review:original-safety", "Original-file safety, desktop roots, capabilities", safety_files));
    jobs.push(review_job("review:tests", "Test coverage and false-green risks for the folder-import client loop", test_files));
    let results = parallel(jobs);
    let raw = collect_raw(results);
    log(raw.len().to_string() + " unique in-scope findings from review panel round " + round.to_string());

    let confirmed = [];
    if raw.len() > 0 {
        let ranked = [];
        ranked = append_sev(raw, "bug", ranked, max_verify());
        ranked = append_sev(raw, "suggestion", ranked, max_verify());
        ranked = append_sev(raw, "nit", ranked, max_verify());
        let dropped = raw.len() - ranked.len();
        if dropped > 0 { log("Capped verify set; dropped " + dropped.to_string() + " lower-severity findings"); }

        phase("Verify");
        let vjobs = [];
        let v_i = 0;
        while v_i < ranked.len() {
            let f = ranked[v_i];
            let vp = "";
            vp += "You are an adversarial skeptic. Repo: " + repo_path() + "\n";
            vp += "THIS STAGE capability_mode=read-only. Do not edit anything.\n";
            vp += "Independently re-read the shipped code on branch " + branch_name() + ".\n";
            vp += "Do not trust the finding. Default real=false unless you personally inspect concrete evidence.\n";
            vp += "Use read_file/grep on the cited file and related call sites.\n";
            vp += "Finding JSON:\n";
            vp += json_encode(f);
            vp += "\nSet real=true only if the defect exists in current HEAD code and is in-scope Phase 2.\n";
            vp += "Folder-duplication that is already fixed (empty-path finalize + tests asserting 2 copies) is real=false.\n";
            vp += "Missing Phase 3-5 is real=false. If the line number is wrong but the bug is real, real=true and put the correct file:line in evidence.\n";
            vp += "If tests already prevent the failure, or the claim misreads the code, real=false.\n";
            vp += "Return severity bug|suggestion|nit for the live defect (may downgrade).\n";
            let vjob = verify_opts("verify:" + as_str(f.file));
            vjob.prompt = vp;
            vjobs.push(vjob);
            v_i += 1;
        }
        let verdicts = parallel(vjobs);
        let i = 0;
        while i < verdicts.len() {
            let v = verdicts[i];
            if v != () && v.success && v.output != () && v.output.real == true && as_str(v.output.evidence) != "" {
                let item = ranked[i];
                if v.output.severity != () {
                    item.severity = v.output.severity;
                }
                confirmed.push(item);
            }
            i += 1;
        }
        log(confirmed.len().to_string() + "/" + ranked.len().to_string() + " findings survived verification");
    }

    let bugs = count_sev(confirmed, "bug");
    let suggestions = count_sev(confirmed, "suggestion");
    let nits = count_sev(confirmed, "nit");
    last_confirmed = confirmed;
    last_bugs = bugs;
    last_suggestions = suggestions;
    last_nits = nits;

    let hand = agent(handoff_prompt(round, json_encode(confirmed), bugs, suggestions, nits), docs_opts("phase2-handoff-" + round.to_string()));
    if !stage_ok(hand) {
        pause("no_progress", "Handoff failed on round " + round.to_string() + ". A resume will re-pause until this journaled result changes.");
    }

    if bugs == 0 {
        outcome = "clean";
    } else {
        let fp = gating_fingerprint(confirmed);
        if last_fp != "" && fp == last_fp {
            stall += 1;
            log("Gating fingerprint unchanged; stall=" + stall.to_string());
        } else {
            stall = 0;
        }
        last_fp = fp;
        if stall >= stall_limit() {
            outcome = "blocked-stall";
        } else if round == requested_rounds {
            outcome = "blocked-cap";
        } else {
            phase("Repair");
            let gating = [];
            let gi = 0;
            while gi < confirmed.len() {
                if is_gating(as_str(confirmed[gi].severity)) {
                    gating.push(confirmed[gi]);
                }
                gi += 1;
            }
            let repair = agent(repair_prompt(round, json_encode(gating)), code_opts("phase2-repair-r" + round.to_string()));
            if !stage_ok(repair) {
                pause("no_progress", "Repair failed on round " + round.to_string() + ". A resume will re-pause until this journaled result changes.");
            }
            round += 1;
        }
    }
}

phase("Close-out");
let close = agent(closeout_prompt(outcome, json_encode(last_confirmed), last_bugs), docs_opts("phase2-closeout"));
if !stage_ok(close) {
    pause("no_progress", "Close-out failed. A resume will re-pause until this journaled result changes.");
}

complete(#{
    summary: "Phase 2 code-review loop finished with outcome=" + outcome,
    outcome: outcome,
    rounds: round,
    bugs: last_bugs,
    suggestions: last_suggestions,
    nits: last_nits,
    handoff: "docs/plans/2026-08-18-desktop-packaging.md",
    branch: branch_name(),
    pr: "https://github.com/joe-cheung-cae/frame-pilot/pull/38",
});
