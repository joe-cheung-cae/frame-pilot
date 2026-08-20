let meta = #{
    name: "desktop-review-fix-loop",
    description: "Bounded review to code to re-review loop on feature/desktop-packaging until P0=0 and P1=0, with per-stage write-allowlists and GitHub comment sync",
    when_to_use: "New adversarial review of live desktop-packaging HEAD, then fix confirmed P0/P1 until a clean re-review",
    phases: [
        #{ title: "GitHub pull", detail: "Read #30-#36 bodies and comments into handoff" },
        #{ title: "Review", detail: "Six-area parallel reviewers; read-only; P0-P3" },
        #{ title: "Verify", detail: "Adversarial skeptic per finding; read-only" },
        #{ title: "Handoff", detail: "Write this-round review markdown and STATUS" },
        #{ title: "Fix", detail: "Backlog then serial tests-first slices if P0/P1 remain" },
        #{ title: "Close-out", detail: "GitHub comments; STATUS; no PR; no issue close" },
    ],
};

fn max_rounds() { 3 }
fn max_verify() { 12 }
fn max_code_slices() { 4 }
fn stall_limit() { 2 }
fn repo_path() { "/Users/chao/workspace/repo/frame-pilot" }
fn branch_name() { "feature/desktop-packaging" }
fn base_ref() { "origin/main" }
fn parent_issue() { "joe-cheung-cae/frame-pilot#30" }
fn scratch_path() { "/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-883235f68017/implementer" }

fn findings_schema() {
    #{
        "type": "object",
        "required": ["findings"],
        "properties": #{
            "findings": #{
                "type": "array",
                "maxItems": 6,
                "items": #{
                    "type": "object",
                    "required": ["file", "line", "severity", "category", "title", "issue", "suggestion", "evidence", "prior_id"],
                    "properties": #{
                        "file": #{ "type": "string" },
                        "line": #{ "type": "integer" },
                        "severity": #{ "type": "string", "enum": ["P0", "P1", "P2", "P3"] },
                        "category": #{ "type": "string" },
                        "title": #{ "type": "string" },
                        "issue": #{ "type": "string" },
                        "suggestion": #{ "type": "string" },
                        "evidence": #{ "type": "string" },
                        "prior_id": #{ "type": "string" },
                        "github_issue": #{ "type": "string" },
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
            "severity": #{ "type": "string", "enum": ["P0", "P1", "P2", "P3"] },
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
            "p0": #{ "type": "integer" },
            "p1": #{ "type": "integer" },
            "p2": #{ "type": "integer" },
            "p3": #{ "type": "integer" },
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
    sev == "P0" || sev == "P1"
}

fn path_in_scope(p) {
    if p == () { return false; }
    if type_of(p) != "string" { return false; }
    if p == "" { return false; }
    if p == "apps/desktop/package-lock.json" { return false; }
    if p == "apps/desktop/src-tauri/Cargo.lock" { return false; }
    if p == "package.json" { return true; }
    let head5 = p.sub_string(0, 5);
    let head6 = p.sub_string(0, 6);
    let head8 = p.sub_string(0, 8);
    head5 == "apps/" || head6 == "tests/" || head8 == "scripts/"
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

fn permissions_block() {
    let s = "";
    s += "FILE PERMISSIONS (host has no kernel ACL; you MUST obey this allowlist):\n";
    s += "Scratch is user-private chmod 700: " + scratch_path() + " — never shared /tmp.\n";
    s += "mkdir -p that scratch dir; chmod 700 it. Copy captures there.\n";
    s += "Review/Verify stages: capability_mode=read-only. Do not write production code. Do not commit.\n";
    s += "GitHub-pull write-allowlist: docs/handoff/loop-github.md ; docs/handoff/STATUS.md ; .grok/workflows/desktop-review-fix-loop.rhai\n";
    s += "Handoff write-allowlist: docs/handoff/loop-round-N-review.md ; docs/handoff/STATUS.md\n";
    s += "Requirements write-allowlist: docs/handoff/loop-round-N-requirements.md ; docs/handoff/STATUS.md\n";
    s += "Backlog write-allowlist: docs/handoff/loop-round-N-backlog.md ; docs/handoff/STATUS.md\n";
    s += "Code write-allowlist: ONLY files listed in that slice (must be under apps/desktop/src-tauri, apps/web, apps/api, tests/, scripts/) plus docs/handoff/STATUS.md\n";
    s += "Retest write-allowlist: docs/handoff/STATUS.md\n";
    s += "GitHub-sync / Close-out write-allowlist: docs/handoff/STATUS.md ; docs/handoff/loop-closeout.md\n";
    s += "FORBIDDEN unless a slice names them: original photos, lockfiles as the only change, APP_VERSION, output export, FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME.\n";
    s += "Do not close GitHub issues. Do not open a PR. Do not merge to main.\n";
    s
}

fn shared_rules() {
    let s = "";
    s += "Repo: " + repo_path() + "\n";
    s += "Branch MUST stay " + branch_name() + ". Confirm with git rev-parse --abbrev-ref HEAD.\n";
    s += "Base: " + base_ref() + ". isolation_worktree is false. Edit the shared workspace.\n";
    s += permissions_block();
    s += "English for code, comments, tests, docs, commits. Local-first. Never modify or delete original photos.\n";
    s += "No cloud, login, payment, bundled models, HEIC/RAW/XMP. Do not start desktop Phases 2-5. Do not bump APP_VERSION.\n";
    s += "Do not redo D1.01-D1.09 unless those defects still exist on current HEAD.\n";
    s += "Already-fixed F001-F006 (joe-cheung-cae/frame-pilot#33 #35 #36 #34 #31 #32) are NOT new P0/P1 unless they still exist on CURRENT HEAD. Read the live source.\n";
    s += "Missing Phase 2-5 work is not a defect. P2/P3 are recorded, not loop-gating.\n";
    s += "Severity: P0 = blocker on HEAD (original-file mutation/deletion, bind not loopback, path-escape/allowlist hole, data loss, orphan sidecar, unconfirmed import cancel, or other Phase-1 correctness/security breakage that still exists).\n";
    s += "P1 = high must-fix reliability/correctness of already-shipped Phase 1 behavior on HEAD.\n";
    s += "P2/P3 = medium/low.\n";
    s += "npm run verify must stay rust-free. Sidecar binds 127.0.0.1 only. Absolute --data-dir. Shipped spawn never --port 0.\n";
    s += "Import cancel stays cooperative. Quit-anyway / SIGTERM is failed + retryable, not cancelled. Processing jobs have no cancel route.\n";
    s += "Always write owner/repo#N. Do not invent issue numbers.\n";
    s += "Do not add Co-authored-by Cursor trailers.\n";
    s += "After every finished write stage: git add only allowlisted files, commit, git push -u origin HEAD.\n";
    s += "If push fails, write the exact error to " + scratch_path() + "/git-push.txt and still finish local handoff.\n";
    s += "Append git log --oneline origin/main..HEAD and git status -sb to " + scratch_path() + "/git-stage-commits.txt after every push.\n";
    s += "If nothing is staged, do not make an empty commit.\n";
    s += "Handoff is the only memory: later stages start from docs/handoff files and GitHub comments, not conversation.\n";
    s
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

fn docs_opts(label) {
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

fn code_opts(label) {
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

fn sync_opts(label) {
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

fn reviewer_rules() {
    let s = "";
    s += "You are a meticulous code reviewer. Check correctness first, style second.\n";
    s += shared_rules();
    s += "THIS STAGE capability_mode=read-only. Do not edit files. Do not commit. Do not push. Do not create GitHub issues.\n";
    s += "Use read_file, grep, list_dir, and run_terminal_command for git diff/log/show and read-only gh.\n";
    s += "Do not answer from memory. Read live source plus GitHub issue bodies AND comments for " + parent_issue() + " and #31 #32 #33 #34 #35 #36 before classifying.\n";
    s += "Commands: cd " + repo_path() + " && git rev-parse --abbrev-ref HEAD && git rev-parse HEAD && git merge-base " + base_ref() + " HEAD && git -c core.quotepath=false diff " + base_ref() + "...HEAD -- <your files>.\n";
    s += "Then read_file each listed source file (not lockfiles) and enough call sites to trace side effects.\n";
    s += "An empty findings list is valid ONLY after you have read the code, the diff, and the GitHub comments.\n";
    s += "Do not invent issues. Do not inflate severity. Do not treat still-open GitHub issues as still-broken without reading HEAD.\n";
    s += "prior_id: F001 F002 F003 F004 F005 F006 if this is that same defect still on HEAD, else empty string.\n";
    s += "github_issue: existing joe-cheung-cae/frame-pilot#N if it is the same defect, else new.\n";
    s += "Every finding must cite a real file path and a RIGHT-side line number you inspected.\n";
    s += "Return at most 6 findings. Prefer fewer confirmed defects over speculative nits.\n";
    s
}

fn review_job(label, focus, files) {
    let p = "";
    p += reviewer_rules();
    p += "Mode: branch. Target: " + branch_name() + " vs " + base_ref() + ".\n";
    p += "Dimension: " + focus + "\n";
    p += "Inspect these files (skip if a path is absent):\n";
    p += files;
    p += "\nReport JSON findings with file, line, severity (P0|P1|P2|P3), category, title, issue, suggestion, evidence, prior_id.\n";
    p += "category should be one of: bug, reliability, security, performance, ux, testing, architecture.\n";
    p += "evidence must quote what you read (function name, condition, or short snippet) — not a guess.\n";
    let job = review_opts(label);
    job.prompt = p;
    job
}

fn stage_ok(r) {
    r != () && r.success
}

fn github_pull_prompt() {
    let s = "";
    s += "You are grok-4.6 for stage GitHub pull.\n";
    s += shared_rules();
    s += "THIS STAGE write-allowlist: docs/handoff/loop-github.md ; docs/handoff/STATUS.md ; .grok/workflows/desktop-review-fix-loop.rhai\n";
    s += "capability_mode=all because gh plus git commit are required; do NOT patch Rust/TS/Python.\n";
    s += "Confirm branch " + branch_name() + " and record full HEAD SHA.\n";
    s += "Pull via gh (not invented URLs): joe-cheung-cae/frame-pilot#30 #31 #32 #33 #34 #35 #36 — bodies AND comments.\n";
    s += "Write docs/handoff/loop-github.md with: HEAD SHA, each issue number as owner/repo#N, title, state (must stay open), body summary, every comment URL and a short digest, and that F001-F006 close-out comments already record fix SHAs.\n";
    s += "mkdir -p " + scratch_path() + " && chmod 700 " + scratch_path() + ".\n";
    s += "Copy the gh JSON dump if present at " + scratch_path() + "/github-issues-pull.json.txt ; if missing, run gh yourself and save it there.\n";
    s += "Write/replace docs/handoff/STATUS.md with: current_stage=GitHub pull, next_stage=Review, branch=" + branch_name() + ", parent_issue=" + parent_issue() + ", round=1, live HEAD SHA, timestamp ISO-8601 with timezone (date '+%Y-%m-%dT%H:%M:%S%z' then format offset as +08:00).\n";
    s += "If .grok/workflows/desktop-review-fix-loop.rhai exists, include it in this commit.\n";
    s += "Commit message exactly: docs: start desktop review-fix loop and pull GitHub comments\n";
    s += "Then git push -u origin HEAD. Append log+status to scratch git-stage-commits.txt.\n";
    s += "Return ok, stage=GitHub pull, commit=full sha, handoff=docs/handoff/STATUS.md, notes=summary of comment URLs.\n";
    s
}

fn handoff_prompt(round, head, confirmed_json, p0, p1, p2, p3) {
    let s = "";
    s += "You are grok-4.6 for stage Handoff of review round " + round.to_string() + ".\n";
    s += shared_rules();
    s += "THIS STAGE write-allowlist: docs/handoff/loop-round-" + round.to_string() + "-review.md ; docs/handoff/STATUS.md\n";
    s += "Do not patch Rust/TS/Python. Do not retick closed review-fix-* Phase-1 boxes as new product work.\n";
    s += "Read docs/handoff/loop-github.md, docs/handoff/STATUS.md, live HEAD (git rev-parse HEAD, expected " + head + ").\n";
    s += "Confirmed findings JSON (already adversarially verified; do not add extras):\n";
    s += confirmed_json;
    s += "\nCounts from the orchestrator: P0=" + p0.to_string() + " P1=" + p1.to_string() + " P2=" + p2.to_string() + " P3=" + p3.to_string() + ".\n";
    s += "Write docs/handoff/loop-round-" + round.to_string() + "-review.md in English with: branch " + branch_name() + ", live HEAD SHA, parent " + parent_issue() + ", that this is a NEW review of current HEAD (not the 2026-08-20 review of 7e545f8), F001-F006 checked against CURRENT code with a table (still-present or fixed), finding index (P0/P1/P2/P3), evidence, GitHub mapping (comment on existing issue if same defect; new issue only for new confirmed P0/P1), and totals.\n";
    s += "If P0=0 and P1=0, say so explicitly. Empty list is valid only because reviewers read the code.\n";
    s += "Copy that review file to " + scratch_path() + "/rereview.md AND " + scratch_path() + "/handoff-copy/.\n";
    s += "Update STATUS.md: current_stage=Handoff, next_stage=Fix or Close-out, round, P0/P1 counts, HEAD SHA, timestamp ISO-8601 with timezone.\n";
    s += "Commit message exactly: docs: record desktop review-fix loop round-" + round.to_string() + " review\n";
    s += "Push. Return ok, stage=Handoff, commit=sha, handoff=docs/handoff/STATUS.md, notes=summary, p0/p1/p2/p3.\n";
    s
}

fn backlog_prompt(round, confirmed_json) {
    let s = "";
    s += "You are grok-4.6 for stage Backlog of round " + round.to_string() + ".\n";
    s += shared_rules();
    s += "THIS STAGE write-allowlist: docs/handoff/loop-round-" + round.to_string() + "-requirements.md ; docs/handoff/loop-round-" + round.to_string() + "-backlog.md ; docs/handoff/STATUS.md\n";
    s += "Do not patch Rust/TS/Python.\n";
    s += "Read the round review file and confirmed JSON:\n";
    s += confirmed_json;
    s += "\nWrite requirements then backlog. Each P0/P1 slice must include: id, severity, depends-on, write-allowlist (concrete paths), implement, tests-first (drive shipped functions; no mock of unit under test; no re-implement oracle), commit-hint, done-when.\n";
    s += "P2/P3 are recorded as non-gating leftover, not slices.\n";
    s += "Update STATUS.md: current_stage=Backlog, next_stage=Code, timestamp ISO-8601 with timezone.\n";
    s += "Commit message exactly: docs: archive desktop review-fix loop round-" + round.to_string() + " backlog\n";
    s += "Push. Return ok, stage=Backlog, commit=sha, handoff=docs/handoff/STATUS.md, notes=slice list.\n";
    s
}

fn code_prompt(round, slice_index, finding_json) {
    let s = "";
    s += "You are grok-4.6 high-effort for Code slice " + slice_index.to_string() + " of round " + round.to_string() + ".\n";
    s += shared_rules();
    s += "Finding JSON:\n";
    s += finding_json;
    s += "\nTHIS STAGE write-allowlist: the cited file plus its existing test module under apps/desktop/src-tauri (#[cfg(test)] same style), plus matching tests under apps/web or apps/api or tests/ ONLY if the finding cites those trees, plus docs/handoff/STATUS.md.\n";
    s += "Do not start Phases 2-5. Tests first. Drive shipped functions. Do not mock the unit under test. Do not re-implement the oracle. No hardcoded expected blobs that skip the code.\n";
    s += "Run cargo test in apps/desktop/src-tauri if you touched Rust. Capture " + scratch_path() + "/cargo-test-round-" + round.to_string() + "-slice-" + slice_index.to_string() + ".txt.\n";
    s += "If rustc/cargo missing (exit 127), capture " + scratch_path() + "/tauri-toolchain.txt and do not claim Rust tests passed.\n";
    s += "npm run test:web / npm run verify only if those trees were touched. verify must stay rust-free.\n";
    s += "Commit with a conventional English subject matching the slice commit-hint. Push.\n";
    s += "Return ok, stage=Code, commit=sha, handoff=docs/handoff/STATUS.md, notes=what changed and tests.\n";
    s
}

fn retest_prompt(round) {
    let s = "";
    s += "You are grok-4.6 high-effort for Retest of round " + round.to_string() + ".\n";
    s += shared_rules();
    s += "THIS STAGE write-allowlist: docs/handoff/STATUS.md\n";
    s += "If production Rust changed this round: cargo test in apps/desktop/src-tauri TWICE. Both exit 0. Capture " + scratch_path() + "/cargo-test-1.txt and cargo-test-2.txt. New tests must be included.\n";
    s += "If rustc/cargo missing (exit 127), capture " + scratch_path() + "/tauri-toolchain.txt ; do not claim Rust tests passed.\n";
    s += "If web/API/scripts were touched, run those suites and capture test-web.log / verify.log. npm run verify must stay rust-free.\n";
    s += "Update STATUS.md tests_run. current_stage=Retest, next_stage=Review, timestamp ISO-8601 with timezone.\n";
    s += "Commit message exactly: test: verify desktop review-fix loop round-" + round.to_string() + "\n";
    s += "Push. Return ok, stage=Retest, commit=sha, notes=commands and results.\n";
    s
}

fn github_sync_prompt(round, head, confirmed_json, p0, p1, kind) {
    let s = "";
    s += "You are grok-4.6 for GitHub sync (" + kind + ") round " + round.to_string() + ".\n";
    s += shared_rules();
    s += "THIS STAGE write-allowlist: docs/handoff/STATUS.md ; docs/handoff/loop-closeout.md\n";
    s += "Do not close issues. Do not open a PR. Do not merge to main.\n";
    s += "HEAD: " + head + "\n";
    s += "Confirmed JSON:\n";
    s += confirmed_json;
    s += "\nP0=" + p0.to_string() + " P1=" + p1.to_string() + ".\n";
    s += "Create GitHub issues ONLY for NEW confirmed P0/P1 that are not the same defect as #31-#36. Comment on an existing issue if it is the same defect. Use gh issue comment / gh issue create. Always write owner/repo#N.\n";
    s += "After each fix round and at close-out, comment on " + parent_issue() + " with: round, HEAD SHA, tests run, evidence path, P0/P1 counts.\n";
    s += "If gh cannot write, capture the exact error to " + scratch_path() + "/github-sync.txt and still finish local handoff — do not fabricate comment URLs.\n";
    s += "Otherwise capture comment URLs and bodies to " + scratch_path() + "/github-sync.txt.\n";
    s += "If kind is close-out and P0=P1=0, write docs/handoff/loop-closeout.md and set STATUS current_stage=Close-out, status=complete, next_stage=none.\n";
    s += "If kind is blocked, STATUS status=blocked, list remaining P0/P1, next_stage=none. That is NOT a pass.\n";
    s += "Commit message exactly: docs: sync GitHub comments for desktop review-fix loop round-" + round.to_string() + "\n";
    s += "Push. Return ok, stage=GitHub sync, commit=sha, notes=comment URLs or exact gh error.\n";
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

phase("GitHub pull");
log("Pulling GitHub issue bodies and comments; chmod 700 scratch");
let pull = agent(github_pull_prompt(), docs_opts("loop-github-pull"));
if !stage_ok(pull) {
    pause("no_progress", "GitHub pull failed; inspect before Review. A resume will re-pause until this journaled result changes.");
}

let round = 1;
let last_fp = "";
let stall = 0;
let outcome = "running";
let last_confirmed = [];
let last_p0 = 0;
let last_p1 = 0;
let last_p2 = 0;
let last_p3 = 0;
let last_head = "";

while round <= requested_rounds && outcome == "running" {
    phase("Review");
    log("Review round " + round.to_string() + " of live " + branch_name() + " HEAD");

    let sidecar_files = "";
    sidecar_files += "- apps/desktop/src-tauri/src/sidecar.rs\n";
    sidecar_files += "- apps/desktop/src-tauri/src/lib.rs\n";
    sidecar_files += "- apps/desktop/src-tauri/src/data_dir.rs\n";
    sidecar_files += "- apps/desktop/src-tauri/tauri.conf.json\n";
    sidecar_files += "- apps/desktop/src-tauri/capabilities/default.json\n";
    sidecar_files += "- apps/desktop/src-tauri/Cargo.toml\n";
    sidecar_files += "Re-check F001/F002/F006 against CURRENT HEAD (SpawnedSidecar Drop, store_child terminate, supervisor_tick_after_probe).\n";

    let adapter_files = "";
    adapter_files += "- apps/web/src/lib/api.ts apps/web/src/lib/apiBase.ts apps/web/src/lib/shell.ts\n";
    adapter_files += "- apps/web/src/lib/navigation.ts apps/web/src/lib/navigation.next.tsx\n";
    adapter_files += "- apps/desktop/src/App.tsx main.tsx router.tsx navigation.router.tsx vite.config.ts\n";

    let job_files = "";
    job_files += "- apps/api/app/services/jobs.py\n";
    job_files += "- apps/api/app/services/importing.py\n";
    job_files += "- apps/api/tests/test_job_reliability.py\n";
    job_files += "- apps/desktop/src-tauri/src/sidecar.rs (cancel/quit/close_decision/quit_dialog_script)\n";
    job_files += "- apps/desktop/src-tauri/src/lib.rs (window close / ExitRequested / handle_close_requested)\n";
    job_files += "Re-check F003/F004/F005 against CURRENT HEAD.\n";

    let security_files = "";
    security_files += "- apps/desktop/src-tauri/src/data_dir.rs sidecar.rs lib.rs\n";
    security_files += "- apps/desktop/src-tauri/capabilities/default.json tauri.conf.json\n";
    security_files += "- apps/web/src/lib/api.ts apiBase.ts shell.ts\n";
    security_files += "- apps/api/app/services/importing.py jobs.py\n";
    security_files += "Check: original photos never mutated/deleted; sidecar binds loopback only; no --port 0 in shipped spawn; absolute --data-dir; CORS/origin; capabilities; FRAMEPILOT_DESKTOP; path-escape; no cloud/upload.\n";

    let test_files = "";
    test_files += "- apps/desktop/src-tauri/src/sidecar.rs #[cfg(test)]\n";
    test_files += "- apps/web/src/lib/api.test.ts apiBase.test.ts navigation.test.tsx shell.test.ts\n";
    test_files += "- apps/api/tests/test_job_reliability.py\n";
    test_files += "- tests/desktop/smoke.sh scripts/dev-desktop.sh package.json\n";

    let pack_files = "";
    pack_files += "- apps/desktop/package.json vite.config.ts tsconfig.json tailwind.config.ts postcss.config.js\n";
    pack_files += "- package.json scripts/dev-desktop.sh tests/desktop/smoke.sh\n";

    let jobs = [];
    jobs.push(review_job("review:sidecar-rust", "Tauri sidecar lifecycle, ready-line, health, shutdown, single-instance, window state", sidecar_files));
    jobs.push(review_job("review:web-adapters", "API base at call time, desktop shell detection, navigation adapter, router reuse of web components", adapter_files));
    jobs.push(review_job("review:jobs-quit", "Quit/cancel/drain, import interrupt reset, processing failure reset, close dialog semantics", job_files));
    jobs.push(review_job("review:security", "Local-first, original-file safety, loopback bind, capabilities, data dir, origin checks", security_files));
    jobs.push(review_job("review:tests", "Test coverage and false-green risks for Phase 1 desktop behavior", test_files));
    jobs.push(review_job("review:packaging", "Desktop Vite/Tauri packaging, shared CSS/tokens, scripts, smoke harness", pack_files));
    let results = parallel(jobs);
    let raw = collect_raw(results);
    log(raw.len().to_string() + " unique in-scope findings from review panel round " + round.to_string());

    let confirmed = [];
    if raw.len() > 0 {
        let ranked = [];
        ranked = append_sev(raw, "P0", ranked, max_verify());
        ranked = append_sev(raw, "P1", ranked, max_verify());
        ranked = append_sev(raw, "P2", ranked, max_verify());
        ranked = append_sev(raw, "P3", ranked, max_verify());
        let dropped = raw.len() - ranked.len();
        if dropped > 0 { log("Capped verify set; dropped " + dropped.to_string() + " lower-severity findings"); }

        phase("Verify");
        let vjobs = [];
        let v_i = 0;
        while v_i < ranked.len() {
            let f = ranked[v_i];
            let vp = "";
            vp += "You are an adversarial skeptic. Repo: " + repo_path() + "\n";
            vp += permissions_block();
            vp += "THIS STAGE capability_mode=read-only. Do not edit anything.\n";
            vp += "Independently re-read the shipped code on branch " + branch_name() + ".\n";
            vp += "Do not trust the finding. Default real=false unless you personally inspect concrete evidence.\n";
            vp += "Use read_file/grep on the cited file and related call sites.\n";
            vp += "Read GitHub comments for " + parent_issue() + " / #31-#36 if the finding claims F001-F006 still exist.\n";
            vp += "Finding JSON:\n";
            vp += json_encode(f);
            vp += "\nSet real=true only if the defect exists in current HEAD code, is in-scope, and is not a missing Phase 2-5 feature.\n";
            vp += "Already-fixed F001-F006 are real=false unless they still exist on current HEAD.\n";
            vp += "If the line number is wrong but the bug is real, still set real=true and put the correct file:line in evidence.\n";
            vp += "If tests already prevent the failure, or the claim misreads the code, real=false.\n";
            vp += "Return severity P0|P1|P2|P3 for the live defect (may downgrade).\n";
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

    let p0 = count_sev(confirmed, "P0");
    let p1 = count_sev(confirmed, "P1");
    let p2 = count_sev(confirmed, "P2");
    let p3 = count_sev(confirmed, "P3");
    last_confirmed = confirmed;
    last_p0 = p0;
    last_p1 = p1;
    last_p2 = p2;
    last_p3 = p3;

    phase("Handoff");
    let hand = agent(handoff_prompt(round, last_head, json_encode(confirmed), p0, p1, p2, p3), docs_opts("loop-handoff-" + round.to_string()));
    if !stage_ok(hand) {
        pause("no_progress", "Handoff failed on round " + round.to_string() + ". A resume will re-pause until this journaled result changes.");
    }

    if p0 + p1 == 0 {
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
            phase("Fix");
            let back = agent(backlog_prompt(round, json_encode(confirmed)), docs_opts("loop-backlog-" + round.to_string()));
            if !stage_ok(back) {
                pause("no_progress", "Backlog failed on round " + round.to_string() + ". A resume will re-pause until this journaled result changes.");
            }
            let gating = [];
            let gi = 0;
            while gi < confirmed.len() {
                if is_gating(as_str(confirmed[gi].severity)) {
                    gating.push(confirmed[gi]);
                }
                gi += 1;
            }
            let slice = 0;
            while slice < gating.len() && slice < max_code_slices() {
                let code = agent(code_prompt(round, slice + 1, json_encode(gating[slice])), code_opts("loop-code-r" + round.to_string() + "-s" + (slice + 1).to_string()));
                if !stage_ok(code) {
                    pause("no_progress", "Code slice failed; inspect before the next slice. A resume will re-pause until this journaled result changes.");
                }
                slice += 1;
            }
            let retest = agent(retest_prompt(round), code_opts("loop-retest-" + round.to_string()));
            if !stage_ok(retest) {
                pause("no_progress", "Retest failed. A resume will re-pause until this journaled result changes.");
            }
            let gsync = agent(github_sync_prompt(round, last_head, json_encode(confirmed), p0, p1, "after-fix"), sync_opts("loop-gsync-" + round.to_string()));
            if !stage_ok(gsync) {
                pause("no_progress", "GitHub sync after fix failed. A resume will re-pause until this journaled result changes.");
            }
            round += 1;
        }
    }
}

phase("Close-out");
let close_kind = "close-out";
if outcome != "clean" {
    close_kind = "blocked";
}
let close = agent(github_sync_prompt(round, last_head, json_encode(last_confirmed), last_p0, last_p1, close_kind), sync_opts("loop-closeout"));
if !stage_ok(close) {
    pause("no_progress", "Close-out failed. A resume will re-pause until this journaled result changes.");
}

complete(#{
    summary: "Desktop review-fix loop finished with outcome=" + outcome,
    outcome: outcome,
    rounds: round,
    p0: last_p0,
    p1: last_p1,
    p2: last_p2,
    p3: last_p3,
    parent_issue: parent_issue(),
    handoff: "docs/handoff/STATUS.md",
    branch: branch_name(),
});
