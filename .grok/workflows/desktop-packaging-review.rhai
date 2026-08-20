let meta = #{
    name: "desktop-packaging-review",
    description: "Full-scale adversarial code review of feature/desktop-packaging vs origin/main, then a structured report",
    when_to_use: "Review the desktop packaging branch before tracking findings on GitHub",
    phases: [
        #{ title: "Review", detail: "parallel reviewers by area" },
        #{ title: "Verify", detail: "adversarial skeptic per finding" },
        #{ title: "Synthesize", detail: "deduped confirmed report" },
    ],
};

fn max_verify() { 12 }
fn repo_path() { "/Users/chao/workspace/repo/frame-pilot" }
fn default_branch() { "feature/desktop-packaging" }
fn default_base() { "origin/main" }

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
                    "required": ["file", "line", "severity", "category", "title", "issue", "suggestion", "evidence"],
                    "properties": #{
                        "file": #{ "type": "string" },
                        "line": #{ "type": "integer" },
                        "severity": #{ "type": "string", "enum": ["high", "medium", "low"] },
                        "category": #{ "type": "string" },
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
        "required": ["real", "reason", "evidence"],
        "properties": #{
            "real": #{ "type": "boolean" },
            "reason": #{ "type": "string" },
            "evidence": #{ "type": "string" },
        },
    }
}

fn report_schema() {
    #{
        "type": "object",
        "required": ["verdict", "summary", "high", "medium", "low", "report_markdown"],
        "properties": #{
            "verdict": #{ "type": "string" },
            "summary": #{ "type": "string" },
            "high": #{ "type": "integer" },
            "medium": #{ "type": "integer" },
            "low": #{ "type": "integer" },
            "report_markdown": #{ "type": "string" },
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
    let file = as_str(f.file);
    let line = as_str(f.line);
    let title = as_str(f.title);
    file + ":" + line + ":" + title
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

fn reviewer_rules() {
    let s = "";
    s += "You are a meticulous code reviewer. Check correctness first, style second.\n";
    s += "Repo: " + repo_path() + "\n";
    s += "Use read-only tools only: read_file, grep, list_dir, and run_terminal_command for git diff/log/show.\n";
    s += "Do not edit files, do not commit, do not push, do not open a PR, do not create GitHub issues.\n";
    s += "Do not answer from memory. Read the listed files and the branch diff before reporting.\n";
    s += "Commands: cd " + repo_path() + " && git rev-parse --abbrev-ref HEAD && git merge-base " + default_base() + " HEAD && git -c core.quotepath=false diff " + default_base() + "...HEAD -- <your files>.\n";
    s += "Then read_file each listed source file (not lockfiles) and enough call sites to trace side effects.\n";
    s += "An empty findings list is valid ONLY after you have read the code and the diff.\n";
    s += "Do not invent issues to fill space. Do not inflate severity. high = actual correctness, security, data-loss, or breakage. medium = real reliability/test gap. low = small but real defect.\n";
    s += "Every finding must cite a real file path and a RIGHT-side line number you inspected.\n";
    s += "Constraints: local-first; never modify or delete original photos; no cloud/login/payment; npm run verify must stay rust-free; APP_VERSION stays 2.0.0-rc2; do not treat missing Phase 2-5 features as bugs.\n";
    s += "Flag race conditions, error-handling gaps, original-file safety, sidecar lifecycle, CORS/origin, data-dir, and quit/cancel behavior.\n";
    s += "Return at most 6 findings. Prefer fewer confirmed defects over speculative nits.\n";
    s
}

fn review_job(label, focus, files) {
    let p = "";
    p += reviewer_rules();
    p += "Mode: branch. Target: " + default_branch() + " vs " + default_base() + ".\n";
    p += "Dimension: " + focus + "\n";
    p += "Inspect these files (skip if a path is absent):\n";
    p += files;
    p += "\nReport JSON findings with file, line, severity (high|medium|low), category, title, issue, suggestion, evidence.\n";
    p += "category should be one of: bug, reliability, security, performance, ux, testing, architecture.\n";
    p += "evidence must quote what you read (function name, condition, or short snippet) — not a guess.\n";
    #{
        prompt: p,
        label: label,
        capability_mode: "read-only",
        output_schema: findings_schema(),
    }
}

fn empty_report(branch, head, reason) {
    let s = "";
    s += "# Full code review — " + branch + "\n\n";
    s += "Branch: `" + branch + "` vs `" + default_base() + "`\n";
    s += "HEAD: `" + head + "`\n\n";
    s += "## Executive summary\n\n";
    s += reason;
    s += "\n\n**Totals:** 0 high · 0 medium · 0 low.\n";
    s += "\nNo confirmed findings survived review/verification.\n";
    s
}

let branch = default_branch();
let base_ref = default_base();
let head = "";
if args != () {
    if args.branch != () { branch = as_str(args.branch); }
    if args.base != () { base_ref = as_str(args.base); }
    if args.head != () { head = as_str(args.head); }
}
if branch == "" { pause("verification", "Pass args.branch — the branch to review."); }

phase("Review");
log("Reviewing " + branch + " vs " + base_ref);

let sidecar_files = "";
sidecar_files += "- apps/desktop/src-tauri/src/sidecar.rs\n";
sidecar_files += "- apps/desktop/src-tauri/src/lib.rs\n";
sidecar_files += "- apps/desktop/src-tauri/src/data_dir.rs\n";
sidecar_files += "- apps/desktop/src-tauri/tauri.conf.json\n";
sidecar_files += "- apps/desktop/src-tauri/capabilities/default.json\n";
sidecar_files += "- apps/desktop/src-tauri/Cargo.toml\n";

let adapter_files = "";
adapter_files += "- apps/web/src/lib/api.ts apps/web/src/lib/apiBase.ts apps/web/src/lib/shell.ts\n";
adapter_files += "- apps/web/src/lib/navigation.ts apps/web/src/lib/navigation.next.tsx\n";
adapter_files += "- apps/web/src/types/globals.d.ts apps/web/src/components/Providers.tsx\n";
adapter_files += "- apps/web/src/components/Shell.tsx ProjectList.tsx ProjectDashboard.tsx\n";
adapter_files += "- apps/web/src/components/ImportPanel.tsx ProcessingPanel.tsx ProjectCreator.tsx CullingWorkspace.tsx\n";
adapter_files += "- apps/web/src/components/HelpShortcuts.tsx apps/web/src/app/help/page.tsx\n";
adapter_files += "- apps/desktop/src/App.tsx main.tsx router.tsx navigation.router.tsx vite.config.ts\n";

let job_files = "";
job_files += "- apps/api/app/services/jobs.py\n";
job_files += "- apps/api/app/services/importing.py\n";
job_files += "- apps/api/tests/test_job_reliability.py\n";
job_files += "- apps/desktop/src-tauri/src/sidecar.rs (cancel/quit/close_decision)\n";
job_files += "- apps/desktop/src-tauri/src/lib.rs (window close / terminate)\n";

let security_files = "";
security_files += "- apps/desktop/src-tauri/src/data_dir.rs sidecar.rs lib.rs\n";
security_files += "- apps/desktop/src-tauri/capabilities/default.json tauri.conf.json\n";
security_files += "- apps/web/src/lib/api.ts apiBase.ts shell.ts\n";
security_files += "- apps/api/app/services/importing.py jobs.py\n";
security_files += "Check: original photos never mutated/deleted; sidecar binds loopback only; no --port 0 in shipped spawn; absolute --data-dir; CORS/origin; capabilities; FRAMEPILOT_DESKTOP; no cloud/upload.\n";

let test_files = "";
test_files += "- apps/web/src/lib/api.test.ts apiBase.test.ts navigation.test.tsx shell.test.ts\n";
test_files += "- apps/web/src/components/*.test.tsx that changed\n";
test_files += "- apps/api/tests/test_job_reliability.py\n";
test_files += "- tests/desktop/smoke.sh scripts/dev-desktop.sh package.json\n";
test_files += "Ask: which D1.01-D1.09 behaviors lack tests; rust-free verify; smoke false greens.\n";

let pack_files = "";
pack_files += "- apps/desktop/package.json vite.config.ts tsconfig.json tailwind.config.ts postcss.config.js\n";
pack_files += "- apps/desktop/index.html src/styles.css src/vite-env.d.ts\n";
pack_files += "- apps/web/tailwind.config.ts apps/web/src/theme/tokens.ts\n";
pack_files += "- package.json scripts/dev-desktop.sh tests/desktop/smoke.sh\n";
pack_files += "Ask: Vite aliases vs Next barrel, Tailwind token fork, verify rust-free, desktop scripts, missing routes.\n";

let jobs = [];
jobs.push(review_job("review:sidecar-rust", "Tauri sidecar lifecycle, ready-line, health, shutdown, single-instance, window state", sidecar_files));
jobs.push(review_job("review:web-adapters", "API base at call time, desktop shell detection, navigation adapter, router reuse of web components", adapter_files));
jobs.push(review_job("review:jobs-quit", "Quit/cancel/drain, import interrupt reset, processing failure reset, close dialog semantics", job_files));
jobs.push(review_job("review:security", "Local-first, original-file safety, loopback bind, capabilities, data dir, origin checks", security_files));
jobs.push(review_job("review:tests", "Test coverage and false-green risks for Phase 1 desktop behavior", test_files));
jobs.push(review_job("review:packaging", "Desktop Vite/Tauri packaging, shared CSS/tokens, scripts, smoke harness", pack_files));
let results = parallel(jobs);

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
log(raw.len().to_string() + " unique in-scope findings from review panel");

if raw.len() == 0 {
    let report = empty_report(branch, head, "The six-area review panel reported no in-scope findings after reading the branch diff.");
    let p = write_scratch_file("review.md", report);
    complete(#{
        summary: "No findings from review panel.",
        path: p,
        confirmed: [],
        high: 0,
        medium: 0,
        low: 0,
        dropped: 0,
    });
}

let ranked = [];
ranked = append_sev(raw, "high", ranked, max_verify());
ranked = append_sev(raw, "medium", ranked, max_verify());
ranked = append_sev(raw, "low", ranked, max_verify());
let dropped = raw.len() - ranked.len();
if dropped > 0 { log("Capped verify set; dropped " + dropped.to_string() + " lower-severity findings"); }

phase("Verify");
let vjobs = [];
let v_i = 0;
while v_i < ranked.len() {
    let f = ranked[v_i];
    let encoded = json_encode(f);
    let vp = "";
    vp += "You are an adversarial skeptic. Repo: " + repo_path() + "\n";
    vp += "Independently re-read the shipped code on branch " + branch + ".\n";
    vp += "Do not trust the finding. Default real=false unless you personally inspect concrete evidence.\n";
    vp += "Use read_file/grep on the cited file and related call sites. Do not edit anything.\n";
    vp += "Finding JSON:\n";
    vp += encoded;
    vp += "\nSet real=true only if the defect exists in current HEAD code, is in-scope for this branch, and is not a missing Phase 2-5 feature.\n";
    vp += "If the line number is wrong but the bug is real, still set real=true and put the correct file:line in evidence.\n";
    vp += "If tests already prevent the failure, or the claim misreads the code, real=false.\n";
    vjobs.push(#{
        prompt: vp,
        label: "verify:" + as_str(f.file),
        capability_mode: "read-only",
        output_schema: verdict_schema(),
    });
    v_i += 1;
}
let verdicts = parallel(vjobs);

let confirmed = [];
let i = 0;
while i < verdicts.len() {
    let v = verdicts[i];
    if v != () && v.success && v.output != () && v.output.real == true && as_str(v.output.evidence) != "" {
        confirmed.push(ranked[i]);
    }
    i += 1;
}
log(confirmed.len().to_string() + "/" + ranked.len().to_string() + " findings survived verification");

phase("Synthesize");
let confirmed_json = json_encode(confirmed);
let sp = "";
sp += "Repo: " + repo_path() + "\n";
sp += "Write the parent tracking issue body for a full code review of branch " + branch + " vs " + base_ref + ".\n";
sp += "HEAD (if known): " + head + "\n";
sp += "Confirmed findings JSON:\n";
sp += confirmed_json;
sp += "\nDo not add findings that are not in that JSON. Do not edit the repo.\n";
sp += "report_markdown must be English GitHub markdown with: Overview, Executive summary, Finding index table (ID F001.., severity, category, title, file:line), Scope notes, Suggested triage order.\n";
sp += "verdict: ship-with-notes | block | clean.\n";
sp += "Count high/medium/low from the JSON only.\n";
sp += "If the array is empty, verdict=clean and say the adversarial panel confirmed nothing.\n";
let synth = agent(sp, #{
    label: "synthesize-report",
    capability_mode: "read-only",
    output_schema: report_schema(),
});

let high = 0;
let medium = 0;
let low = 0;
let c_i = 0;
while c_i < confirmed.len() {
    let sev = as_str(confirmed[c_i].severity);
    if sev == "high" { high += 1; }
    if sev == "medium" { medium += 1; }
    if sev == "low" { low += 1; }
    c_i += 1;
}

let report_text = empty_report(branch, head, "Synthesizer unavailable; confirmed findings are in the structured result.");
let verdict = "ship-with-notes";
let summary = confirmed.len().to_string() + " confirmed findings";
if confirmed.len() == 0 {
    verdict = "clean";
    summary = "No confirmed findings.";
}
if synth != () && synth.success && synth.output != () {
    if as_str(synth.output.report_markdown) != "" { report_text = synth.output.report_markdown; }
    if as_str(synth.output.verdict) != "" { verdict = synth.output.verdict; }
    if as_str(synth.output.summary) != "" { summary = synth.output.summary; }
    if synth.output.high != () { high = synth.output.high; }
    if synth.output.medium != () { medium = synth.output.medium; }
    if synth.output.low != () { low = synth.output.low; }
}

let p = write_scratch_file("review.md", report_text);
complete(#{
    summary: summary,
    verdict: verdict,
    path: p,
    confirmed: confirmed,
    high: high,
    medium: medium,
    low: low,
    dropped: dropped,
    report_markdown: report_text,
});
