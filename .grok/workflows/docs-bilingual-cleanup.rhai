let meta = #{
    name: "docs-bilingual-cleanup",
    description: "Fetch GitHub main, inventory living docs, bilingual Chinese/English pairs, remove stale handoff and superseded plans, review leftover links, open a PR",
    when_to_use: "Clean FramePilot living docs into paired Chinese and English pages and drop completed-loop handoff files",
    phases: [
        #{ title: "GitHub sync", detail: "Confirm feature branch from origin/main and capture git-sync evidence" },
        #{ title: "Inventory", detail: "Classify living markdown versus stale handoff and superseded plans" },
        #{ title: "Cleanup", detail: "Delete completed handoff and superseded plans; retarget remaining links" },
        #{ title: "Bilingual sync", detail: "Add Chinese and English counterparts with matching facts and switcher links" },
        #{ title: "Tests", detail: "Extend markdown-link and release-check tests; run them twice" },
        #{ title: "Review", detail: "Adversarial leftover-link, missing-pair, and tracker-preservation review" },
        #{ title: "PR", detail: "Push the feature branch and open one GitHub pull request against main" },
    ],
};

fn notes_schema() {
    #{
        "type": "object",
        "properties": #{
            "ok": #{ "type": "boolean" },
            "notes": #{ "type": "string" },
        },
    }
}

fn findings_schema() {
    #{
        "type": "object",
        "required": ["findings"],
        "properties": #{
            "findings": #{
                "type": "array",
                "maxItems": 12,
                "items": #{
                    "type": "object",
                    "required": ["file", "issue"],
                    "properties": #{
                        "file": #{ "type": "string" },
                        "issue": #{ "type": "string" },
                        "evidence": #{ "type": "string" },
                    },
                },
            },
        },
    }
}

fn scratch_dir_of(passed) {
    if passed != () && type_of(passed) == "map" && passed.scratch_dir != () && passed.scratch_dir != "" {
        passed.scratch_dir
    } else {
        "/tmp/grok-goal-b0bb6093e4d7/implementer"
    }
}

fn branch_of(passed) {
    if passed != () && type_of(passed) == "map" && passed.branch != () && passed.branch != "" {
        passed.branch
    } else {
        "docs/bilingual-cleanup"
    }
}

fn common_rules(scratch, branch) {
    let s = "";
    s += "You are working in the FramePilot git repository. Resolve the repo root with: git rev-parse --show-toplevel. Do not hardcode /Users/chao/workspace/repo/frame-pilot.\n";
    s += "Current feature branch MUST be " + branch + ". Run git status and git rev-parse --abbrev-ref HEAD before edits. If HEAD is main, checkout " + branch + " from origin/main. NEVER commit on main. NEVER merge into local main. NEVER git push origin main. NEVER force-push.\n";
    s += "Scratch evidence directory: " + scratch + " — mkdir -p it if needed. Write named proof files there. Do not use other shared /tmp paths.\n";
    s += "Use tools. Read the named files with read_file/grep before writing. Do not answer from memory.\n";
    s += "Keep FramePilot local-first. Do not modify original photos. Do not add cloud, login, payment, or model files. Do not change application product code, scoring, grouping, export, or desktop Phase 3-5 implementation. This task is documentation, workflows, and the markdown-link/release-check scripts only.\n";
    s += "Do not delete develop_plan.md. Do not delete docs/plans/2026-08-18-desktop-packaging.md. Preserve every still-open D3-D5 task id and checkbox state in that tracker (including D3.01-D3.07, D4.*, D5.*). Do not retick tracker boxes.\n";
    s += "Do not recreate docs/handoff/STATUS.md or any docs/handoff/* file.\n";
    s += "Code, comments, tests, and commit messages stay English. Living documentation is bilingual after this work.\n";
    s += "If a git commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to Joe Cheung <zhangchao.simzc@outlook.com>. No Co-authored-by trailers.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s
}

fn pairing_rules() {
    let s = "";
    s += "PAIRING CONVENTION: English living pages keep their current path (name.md). Chinese counterpart is the same path with .zh.md (name.zh.md). Example: README.md <-> README.zh.md, docs/api.md <-> docs/api.zh.md, AGENTS.md <-> AGENTS.zh.md.\n";
    s += "Each page MUST include a counterpart switcher near the top. English: `> Language: **English** | [中文](NAME.zh.md)`. Chinese: `> 语言：[English](NAME.md) | **中文`.\n";
    s += "Facts must match across the pair: commands, ports, versions, file types, task ids, checkbox states, API paths, constraints. Do not invent a second architecture. Do not summarize a long page into a stub. Write the complete counterpart.\n";
    s += "Preserve fenced code, bash commands, table structure, and relative links. When a living page has a language pair, same-language links should target the matching counterpart (English -> foo.md, Chinese -> foo.zh.md).\n";
    s += "docs/desktop_development_plan.md is currently Chinese. After this work, docs/desktop_development_plan.md MUST be English and docs/desktop_development_plan.zh.md MUST be Chinese (you may move the current Chinese text into the .zh.md file after retargeting deleted-file links).\n";
    s += "Do not translate deleted stale files. Do not add Chinese copies of files you are supposed to delete.\n";
    s
}

fn living_batches() {
    [
        "README.md and AGENTS.md",
        "develop_plan.md",
        "implement_goals.md",
        "docs/api.md",
        "docs/architecture.md, docs/scoring.md, and docs/export_interoperability.md",
        "docs/desktop_development_plan.md (currently Chinese: English must land at .md, Chinese at .zh.md)",
        "docs/desktop_feasibility_notes.md and docs/desktop_goal_mode.md",
        "docs/plans/2026-08-18-desktop-packaging.md (KEEP the D3-D5 open task ids and all checkbox states)",
        "docs/v1_review_for_v2.md",
        "docs/v2_performance_baseline.md",
        "docs/v2_product_requirements.md, docs/v2_architecture.md, docs/v2_milestones.md, docs/v2_algorithm_strategy.md, docs/v2_testing_strategy.md, docs/v2_migration_plan.md, and docs/v2_known_limitations.md",
        "docs/v2_release_review.md, docs/v2_release_candidate_checklist.md, docs/v2_real_world_validation.md, docs/v2_real_world_validation_notes.md, docs/v2_rc2_validation_decision.md, and docs/templates/algorithm_validation_notes_template.md",
    ]
}

let scratch_dir = scratch_dir_of(args);
let branch = branch_of(args);
let rules = common_rules(scratch_dir, branch);
let pairing = pairing_rules();

phase("GitHub sync");
log("Confirm feature branch from origin/main");
let github_prompt = "";
github_prompt += rules;
github_prompt += "PHASE: GitHub sync.\n";
github_prompt += "1. Run: git fetch origin\n";
github_prompt += "2. Confirm HEAD is branch " + branch + " and is NOT main.\n";
github_prompt += "3. Confirm git merge-base HEAD origin/main equals git rev-parse origin/main (branch was created from that tip; it is OK if later commits exist on the feature branch).\n";
github_prompt += "4. Capture ALL of the following into " + scratch_dir + "/git-sync.txt (create/overwrite or append a clearly labeled second capture if the file already exists from the parent):\n";
github_prompt += "   git fetch origin output; git status -sb; git rev-parse --abbrev-ref HEAD; git merge-base HEAD origin/main; git rev-parse HEAD; git rev-parse origin/main.\n";
github_prompt += "5. If the branch does not exist, create it from origin/main: git checkout -B " + branch + " origin/main then git branch --unset-upstream.\n";
github_prompt += "6. Do not edit documentation in this phase except the evidence file under scratch.\n";
github_prompt += "Return a short notes string with branch name and SHAs.\n";
let github_result = agent(github_prompt, #{
    label: "github-sync",
    capability_mode: "all",
    output_schema: notes_schema(),
});
if github_result == () || !github_result.success {
    log("GitHub sync agent reported failure; continuing with inventory using current workspace state");
}

phase("Inventory");
log("Classify living vs stale documentation");
let inventory_prompt = "";
inventory_prompt += rules;
inventory_prompt += "PHASE: Inventory.\n";
inventory_prompt += "Use list_dir, grep, and bash find/wc to inventory markdown.\n";
inventory_prompt += "Living root pages: README.md, AGENTS.md, develop_plan.md, implement_goals.md.\n";
inventory_prompt += "Living docs/** pages: every docs/**/*.md EXCEPT stale paths listed below.\n";
inventory_prompt += "STALE (delete in the next phase, do not translate): every file under docs/handoff/ (completed Phase 0-2 and review-fix loop artifacts) AND docs/plans/2026-08-18-desktop-packaging-review.md (findings already folded into the tracker; replace remaining pointers with a short historical note on the tracker).\n";
inventory_prompt += "KEEP: develop_plan.md and docs/plans/2026-08-18-desktop-packaging.md (open D3-D5 tracker).\n";
inventory_prompt += "Also list .grok/workflows/*.rhai that still name docs/handoff/* as a live contract.\n";
inventory_prompt += "Write " + scratch_dir + "/doc-inventory.txt with sections: KEPT living English pages, STALE to delete, WORKFLOW files to retarget, NOTES. This inventory may be updated after cleanup/bilingual.\n";
inventory_prompt += "Do not delete or translate files in this phase.\n";
let inventory_result = agent(inventory_prompt, #{
    label: "inventory",
    capability_mode: "all",
    output_schema: notes_schema(),
});
if inventory_result == () || !inventory_result.success {
    log("Inventory agent reported failure; cleanup will use the hardcoded living/stale lists");
}

phase("Cleanup");
log("Delete completed handoff and superseded plans; retarget remaining links");
let cleanup_prompt = "";
cleanup_prompt += rules;
cleanup_prompt += pairing;
cleanup_prompt += "PHASE: Cleanup (redundant docs).\n";
cleanup_prompt += "DELETE these stale paths from the git tree (git rm):\n";
cleanup_prompt += "- the entire docs/handoff/ directory and every file in it (STATUS.md, phase0-*, phase1-*, phase2-*, review-fix-*, loop-*)\n";
cleanup_prompt += "- docs/plans/2026-08-18-desktop-packaging-review.md\n";
cleanup_prompt += "KEEP develop_plan.md and docs/plans/2026-08-18-desktop-packaging.md. Preserve §5.1 open D3-D5 boxes.\n";
cleanup_prompt += "On the tracker header, replace the Opus 5 review file link with a short note that the 2026-08-18 review findings were folded into this plan and the review file was removed as redundant. Do not drop D0.00 start guidance or §5.1.\n";
cleanup_prompt += "UPDATE AGENTS.md in this same change: bilingual living docs are required (English page + matching Chinese *.zh.md, each linking to the other). Code, comments, tests, and commit messages remain English. This objective overrides the old English-only documentation rule.\n";
cleanup_prompt += "Retarget remaining references so living docs and workflows no longer treat docs/handoff/* as the live contract. In particular edit:\n";
cleanup_prompt += "- docs/desktop_goal_mode.md (Phase 2+ prompts currently name docs/handoff/*; point them at docs/plans/2026-08-18-desktop-packaging.md §5.1 as the living tracker. Note that Phase 0-2 are already on main and remaining work is Phase 3-5. Do not instruct agents to recreate handoff STATUS files.)\n";
cleanup_prompt += "- docs/desktop_development_plan.md links to the deleted packaging-review file\n";
cleanup_prompt += "- develop_plan.md and implement_goals.md English-only documentation sentences: living docs are bilingual; code/comments/tests/commits stay English\n";
cleanup_prompt += "- every .grok/workflows/*.rhai EXCEPT this docs-bilingual-cleanup workflow: historical Phase 0-2/review-fix workflows may remain as completed-phase scripts, but replace live-contract handoff paths with the packaging tracker and state that docs/handoff is retired. Do not leave prompts that require writing docs/handoff/STATUS.md.\n";
cleanup_prompt += "Grep the whole repo (md, rhai, sh, ts, py, json) for docs/handoff and 2026-08-18-desktop-packaging-review. Fix remaining living references. Deleted files can mention each other only if they are gone.\n";
cleanup_prompt += "Do not add Chinese counterparts in this phase except you MAY leave AGENTS.md English updated (the bilingual phase writes AGENTS.zh.md).\n";
cleanup_prompt += "After edits: git add the deletions and retargets, commit on " + branch + " with subject: docs: retire completed handoff files and superseded packaging review\n";
cleanup_prompt += "If nothing to commit, skip empty commit.\n";
cleanup_prompt += "Write a short summary of deleted paths into " + scratch_dir + "/doc-inventory.txt (append a DELETED section).\n";
let cleanup_result = agent(cleanup_prompt, #{
    label: "cleanup",
    capability_mode: "all",
    output_schema: notes_schema(),
});
if cleanup_result == () || !cleanup_result.success {
    log("Cleanup agent reported failure; bilingual phase must still skip deleted handoff paths");
}

phase("Bilingual sync");
log("Add Chinese and English counterparts for remaining living pages");
let batches = living_batches();
let bilingual_jobs = [];
let batch_index = 0;
for batch in batches {
    let bp = "";
    bp += rules;
    bp += pairing;
    bp += "PHASE: Bilingual sync. Your exclusive file batch: " + batch + "\n";
    bp += "Read each source file fully with read_file before writing. Translate/create the missing language so BOTH name.md (English) and name.zh.md (Chinese) exist, are non-empty, and share facts.\n";
    bp += "Add the language switcher at the top of BOTH files if missing. Update same-language relative links. Do not retick tracker checkboxes. Do not restore docs/handoff files.\n";
    bp += "Simplified Chinese for .zh.md. Keep identifiers, paths, commands, and task ids untranslated when they are code or file names.\n";
    bp += "Do not git commit. Other batches run in parallel; committing would race. Only write your batch files.\n";
    bp += "If a file in your batch was deleted as stale, skip it.\n";
    bilingual_jobs.push(#{
        prompt: bp,
        label: "bilingual-" + batch_index.to_string(),
        capability_mode: "all",
        output_schema: notes_schema(),
    });
    batch_index += 1;
}
let bilingual_results = parallel(bilingual_jobs);
let bilingual_ok = 0;
for br in bilingual_results {
    if br != () && br.success {
        bilingual_ok += 1;
    }
}
log(bilingual_ok.to_string() + "/" + bilingual_jobs.len().to_string() + " bilingual batches reported success");

phase("Tests");
log("Extend markdown-link and release-check tests");
let tests_prompt = "";
tests_prompt += rules;
tests_prompt += pairing;
tests_prompt += "PHASE: Tests.\n";
tests_prompt += "Extend the EXISTING shipped checker scripts/check-markdown-links.sh (it already embeds Python) and scripts/test-release-checks.sh. Wire-up stays npm run check:markdown-links and npm run test:scripts.\n";
tests_prompt += "The checker must fail when ANY of these hold for the scanned tree (the optional first CLI arg is the tree root, default repo root):\n";
tests_prompt += "(a) a living markdown page lacks a non-empty Chinese counterpart or a non-empty English counterpart. Living scan set: README.md, AGENTS.md, develop_plan.md, implement_goals.md (each if present, including .zh.md variants) plus docs/**/*.md. Pairing: foo.md <-> foo.zh.md. Empty (whitespace-only) files fail. Do not require a golden translation string.\n";
tests_prompt += "(b) known stale paths are present: any file under docs/handoff/, and docs/plans/2026-08-18-desktop-packaging-review.md. Error text must mention the stale path or 'handoff' / 'packaging-review' clearly so tests can expect_failure on a substring.\n";
tests_prompt += "(c) remaining relative markdown links dangle (keep the existing link resolver; ignore http(s)/mailto/anchors/code spans).\n";
tests_prompt += "Also fail if a living page has no markdown link that resolves to its counterpart file.\n";
tests_prompt += "Drive the REAL shipped checker on a fixture tree AND on the real repo. Do not mock the checker. Do not hardcode a full golden translation.\n";
tests_prompt += "Update scripts/test-release-checks.sh: the old success fixture only had English files — add .zh.md counterparts with switcher links so the success case still passes. Add expect_failure cases for missing counterpart, empty counterpart, missing counterpart link, and a present docs/handoff/STATUS.md stale path. Keep existing dangling-link and validation-decision tests.\n";
tests_prompt += "If bilingual files are still missing, create the missing counterparts yourself (same pairing rules) so the real-repo check can pass. Do not leave the suite red.\n";
tests_prompt += "Refresh " + scratch_dir + "/doc-inventory.txt with KEPT living pages (English path + Chinese path) and DELETED stale handoff/plan paths.\n";
tests_prompt += "Then run BOTH of these twice (four process invocations total is OK as long as each pair is captured):\n";
tests_prompt += "  npm run check:markdown-links\n";
tests_prompt += "  npm run test:scripts\n";
tests_prompt += "Capture run 1 combined output to " + scratch_dir + "/doc-checks-1.log and run 2 to " + scratch_dir + "/doc-checks-2.log. Both must exit 0.\n";
tests_prompt += "Commit on " + branch + " with subject: test: fail markdown checks without bilingual pairs or stale handoff paths\n";
tests_prompt += "Include the bilingual doc files in the commit if they are still unstaged. git add relevant files only.\n";
let tests_result = agent(tests_prompt, #{
    label: "tests",
    capability_mode: "all",
    output_schema: notes_schema(),
});
if tests_result == () || !tests_result.success {
    log("Tests agent reported failure; review must still inspect the checker and tree");
}

phase("Review");
log("Adversarial leftover-link and missing-pair review");
let review_jobs = [];
let review_areas = [
    "broken relative markdown links and leftover docs/handoff or packaging-review references in remaining md/rhai/sh files",
    "missing or empty Chinese/English counterparts and missing switcher links on living pages",
    "whether develop_plan.md and the desktop D3-D5 tracker still exist with open task ids D3.01-D5.05 preserved",
];
let area_index = 0;
for area in review_areas {
    let rp = "";
    rp += rules;
    rp += "PHASE: Review (read-only). Area: " + area + "\n";
    rp += "Use grep and read_file on the live tree. Do not answer from memory. Report concrete findings as {file, issue, evidence}. Empty findings is valid ONLY after you grepped and sampled README.md, README.zh.md, AGENTS.md, develop_plan.md, and docs/plans/2026-08-18-desktop-packaging.md (and its .zh.md).\n";
    rp += "Write your notes also to " + scratch_dir + "/review.txt (append, with a heading for your area).\n";
    rp += "capability: inspect only; do not edit in this review agent.\n";
    review_jobs.push(#{
        prompt: rp,
        label: "review-" + area_index.to_string(),
        capability_mode: "read-only",
        output_schema: findings_schema(),
    });
    area_index += 1;
}
let review_results = parallel(review_jobs);
let review_findings = [];
for rr in review_results {
    if rr != () && rr.success && rr.output != () && rr.output.findings != () {
        for f in rr.output.findings {
            review_findings.push(f);
        }
    }
}
log(review_findings.len().to_string() + " review findings reported");

if review_findings.len() > 0 {
    let encoded = json_encode(review_findings);
    let fix_prompt = "";
    fix_prompt += rules;
    fix_prompt += pairing;
    fix_prompt += "PHASE: Review fixes. The review panel reported these JSON findings:\n";
    fix_prompt += encoded + "\n";
    fix_prompt += "Independently inspect each finding. Fix real leftover links, missing pairs, empty counterparts, missing switcher links, and any accidental tracker/develop_plan deletion. Do not recreate docs/handoff. Do not merge to main.\n";
    fix_prompt += "Re-run npm run check:markdown-links and npm run test:scripts. Append output to " + scratch_dir + "/doc-checks-2.log if you had to re-run.\n";
    fix_prompt += "Append what you fixed to " + scratch_dir + "/review.txt.\n";
    fix_prompt += "Commit remaining fixes on " + branch + " with subject: docs: fix bilingual review findings\n";
    let fix_result = agent(fix_prompt, #{
        label: "review-fix",
        capability_mode: "all",
        output_schema: notes_schema(),
    });
    if fix_result == () || !fix_result.success {
        log("Review-fix agent reported failure");
    }
}

phase("PR");
log("Push the feature branch and open a pull request against main");
let pr_prompt = "";
pr_prompt += rules;
pr_prompt += "PHASE: PR.\n";
pr_prompt += "1. git status -sb; git log --oneline origin/main..HEAD; git diff --stat origin/main...HEAD. Write that to " + scratch_dir + "/branch-diff.txt.\n";
pr_prompt += "2. Stage any remaining intended doc/test/workflow files. Do not add secrets, photos, or node_modules. Commit if needed with an English docs: or test: subject.\n";
pr_prompt += "3. Push ONLY this feature branch: git push -u origin " + branch + "\n";
pr_prompt += "   Never push main. Never git merge main.\n";
pr_prompt += "4. Open ONE pull request against main for repo joe-cheung-cae/frame-pilot, head " + branch + ", base main. Title: docs: bilingual living pages and stale handoff cleanup\n";
pr_prompt += "   Body MUST describe bilingual Chinese/English sync AND stale handoff/plan cleanup. Mention that develop_plan.md and the desktop Phase 3-5 tracker remain. Do not close unrelated PR 41.\n";
pr_prompt += "   Prefer gh if it exists. If gh is missing, use GitHub MCP github__create_pull_request (owner joe-cheung-cae, repo frame-pilot, title, head, base main, body). Draft false.\n";
pr_prompt += "5. Capture PR number, URL, and gh pr view or MCP payload to " + scratch_dir + "/pr.txt. Also append a second git status -sb / rev-parse --abbrev-ref HEAD / merge-base capture to " + scratch_dir + "/git-sync.txt labeled AFTER_PR.\n";
pr_prompt += "6. If merging is allowed, merge ONLY through the GitHub PR API (gh pr merge or github__merge_pull_request). Do not git merge into local main. If protection/review blocks merge, capture the exact error to " + scratch_dir + "/pr-merge.txt — an open PR then satisfies merge-via-PR for this environment.\n";
pr_prompt += "7. Confirm README.md, README.zh.md, develop_plan.md, develop_plan.zh.md, docs/plans/2026-08-18-desktop-packaging.md and its .zh.md exist; docs/handoff is gone; packaging-review.md is gone.\n";
let pr_result = agent(pr_prompt, #{
    label: "open-pr",
    capability_mode: "all",
    output_schema: notes_schema(),
});
if pr_result == () || !pr_result.success {
    log("PR agent reported failure; parent must still push and open the PR if the branch has commits");
}

let summary = "docs-bilingual-cleanup finished phases: GitHub sync, inventory, cleanup, bilingual sync, tests, review, PR. branch=" + branch;
complete(#{
    summary: summary,
    branch: branch,
    scratch_dir: scratch_dir,
    bilingual_batches_ok: bilingual_ok,
    review_finding_count: review_findings.len(),
});
