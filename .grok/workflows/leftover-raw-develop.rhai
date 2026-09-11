let meta = #{
    name: "leftover-raw-develop",
    description: "Serial leftover pipeline: 需求拆解, 评审, 归档, 开发, 测试, 上线 for RAW fallback demosaic",
    when_to_use: "Land leftover RAW fallback demosaic (no embedded preview) on feature/leftover-raw-develop without inventing Phase 10",
    phases: [
        #{ title: "Inspect", detail: "Skip stages already committed and pushed" },
        #{ title: "需求拆解", detail: "Bilingual leftover plan + GitHub issue + section 1.1 Next" },
        #{ title: "评审", detail: "Adversarial review against live RAW import path" },
        #{ title: "归档", detail: "Confirm leftover board is ready for 开发" },
        #{ title: "开发", detail: "Tests-first fallback postprocess when extract_thumb fails" },
        #{ title: "测试", detail: "Named pytest + lint:api; no camera files" },
        #{ title: "上线", detail: "Push, draft PR, living docs, issue comment; do not merge" },
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
    "docs: leftover plan for RAW fallback develop"
}

fn subject_review() {
    "docs: review leftover RAW fallback develop"
}

fn subject_archive() {
    "docs: archive leftover RAW fallback develop"
}

fn subject_develop() {
    "feat: demosaic RAW without embedded preview"
}

fn subject_evidence() {
    "docs: record leftover RAW fallback develop"
}

fn plan_en() {
    "docs/plans/2026-09-11-leftover-raw-develop.md"
}

fn plan_zh() {
    "docs/plans/2026-09-11-leftover-raw-develop.zh.md"
}

fn repo_rules() {
    let s = "";
    s += "Resolve the repo with: git rev-parse --show-toplevel. Do not hardcode machine home paths.\n";
    s += "ONE TASK ONLY: leftover RAW fallback develop. Do not invent Phase 10 / S10 / 2.3. Do not reopen S9.04 joe-cheung-cae/frame-pilot#162 as if it were unfinished. Embedded-preview RAW stays extract_thumb only.\n";
    s += "Plan files after 需求拆解: docs/plans/2026-09-11-leftover-raw-develop.md and docs/plans/2026-09-11-leftover-raw-develop.zh.md. Read both before later stages. Discover the GitHub issue number from that plan or gh; never guess the number.\n";
    s += "Branch must stay feature/leftover-raw-develop. Create it from origin/main if missing. Do not checkout main for commits. Do not merge to main. Do not squash. Do not force-push.\n";
    s += "isolation_worktree is false. Edit the shared workspace. Do not create a second worktree.\n";
    s += "Use tools. Read the named files before writing. Do not answer from memory.\n";
    s += "English for code, comments, tests, commits. Bilingual living docs when you touch docs. Local-first. Never modify or delete original photos. Do not commit camera photos, certs, or model weights.\n";
    s += "No cloud upload, login, payment, bundled neural models. Do not bump APP_VERSION. Do not sign. Do not claim SmartScreen-clean or store listing.\n";
    s += "LOCKED: FramePilot is not a RAW editor. No exposure/WB UI. No color-managed pipeline. No extra extensions (.cr2 .raf .orf .rw2). Keep .dng .arw .cr3 .nef only.\n";
    s += "LOCKED: extract_raw_preview_image stays thumb-only and must never call postprocess. Add open_raw_import_image (or equivalent) that tries extract_thumb first, then postprocess only when thumb fails.\n";
    s += "LOCKED postprocess kwargs: use_camera_wb=True, no_auto_bright=True, output_bps=8, half_size=True. Review may tighten; must not add editor controls.\n";
    s += "LOCKED: never postprocess inside expand_import_paths (sync HTTP). RAW extensions collect by suffix. Develop or skip only in register_import_file / import_image_file / import derivative job.\n";
    s += "LOCKED skip reason when thumb AND postprocess fail: RAW file could not be developed; no embedded preview and demosaic failed. Cleanup any originals/ copy. No leftover bytes.\n";
    s += "LOCKED tests: tiny_dng_without_preview_bytes() already builds CFA without JPEG preview. Use it. Garbage bytes still fail both paths. Do not commit camera RAW.\n";
    s += "Keep test_extract_raw_preview_does_not_call_postprocess green for files WITH a preview.\n";
    s += "Out: auto-download/install, processing pool, Redis/Celery, SmartScreen/store, tray/D3.06, APP_VERSION bump, packaged NSIS/DMG, desktop.yml dispatch.\n";
    s += "Do not run git config --global or git config user.name. If commit fails with empty ident, set GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL for that command only to match git log -1 --format='%an <%ae>'.\n";
    s += "Do not add Co-authored-by Cursor or similar trailers.\n";
    s += "YOU ARE NOT READ-ONLY (except the skeptic). agent_type is general-purpose with capability_mode all. You have run_terminal_command, git, gh, search_replace, write, and GitHub MCP (search_tool then github issue/PR tools). Do not return ok=false claiming plan mode, missing bash, missing gh, or missing issue_write. If a tool is missing, try the other (gh CLI or GitHub MCP) before failing.\n";
    s += "GITHUB: after every finished stage commit, git push -u origin HEAD. After the first successful push of this branch, if no open PR exists for head feature/leftover-raw-develop against main, create ONE draft PR: title 'feat: leftover RAW fallback demosaic (no embedded preview)'. Body must say Refs and the leftover issue number once it exists; must not say Fixes or Close. Never open a second PR; later stages only push.\n";
    s += "Scratch: mkdir -p \"$HOME/.cache/framepilot-leftover-raw-develop\" && chmod 700 that directory. Never /tmp for secrets or QA photos. Do not import camera photos.\n";
    s += "Append SHA, subject, push result, and PR URL to $HOME/.cache/framepilot-leftover-raw-develop/git-github.txt after every push.\n";
    s += "If push fails, capture the exact error, retry once, then continue the stage if possible and report the blocker in notes.\n";
    s
}

fn github_tail() {
    let s = "";
    s += "Then git push -u origin HEAD.\n";
    s += "Ensure a single draft PR exists for feature/leftover-raw-develop into main (create if missing, never a second PR). Refs the leftover issue only. Do not say Fixes or Close.\n";
    s += "Append SHA/subject/push/PR to $HOME/.cache/framepilot-leftover-raw-develop/git-github.txt.\n";
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
    s += "Inspect FramePilot leftover RAW fallback develop progress. Use tools. Do not implement product code. Do not commit.\n";
    s += "Read: git rev-parse --show-toplevel; git rev-parse --abbrev-ref HEAD; git log origin/main..HEAD --oneline --format='%s'; ";
    s += "develop_plan.md section 1.1; docs/desktop_development_plan.md section 5.6 and 10; docs/v2_known_limitations.md Deferred Formats; ";
    s += "apps/api/app/image/raw_preview.py; apps/api/app/services/importing.py extract_raw_preview_image call sites; ";
    s += "docs/plans/2026-09-11-leftover-raw-develop.md if it exists.\n";
    s += "Search git log origin/main..HEAD for these exact subjects and set run_* false when that commit already exists, true when the agent must still do the work:\n";
    s += "run_breakdown false if subject 'docs: leftover plan for RAW fallback develop' exists.\n";
    s += "run_review false if subject 'docs: review leftover RAW fallback develop' exists.\n";
    s += "run_archive false if subject 'docs: archive leftover RAW fallback develop' exists.\n";
    s += "run_develop false if subject 'feat: demosaic RAW without embedded preview' exists.\n";
    s += "run_test true unless the develop subject exists AND you have evidence named pytest was already run green for that SHA in notes; when unsure set true.\n";
    s += "run_launch false if subject 'docs: record leftover RAW fallback develop' exists.\n";
    s += "issue: leftover GitHub issue number as a string if the plan or gh issue list shows it, else empty string. Do not guess.\n";
    s += "notes: branch, whether extract_raw_preview_image still never postprocess, and next stage.\n";
    s
}

fn breakdown_prompt() {
    let s = "";
    s += "You are the 需求拆解 agent for FramePilot leftover RAW fallback develop. Documentation contract only. Do not implement production Python yet.\n";
    s += repo_rules();
    s += "You MUST: (1) create or reuse the leftover GitHub issue, (2) checkout feature/leftover-raw-develop, (3) write/update bilingual leftover plans with the real issue number, (4) point develop_plan.md section 1.1 Next at this leftover, (5) git add/commit/push, (6) open the single draft PR. Return ok=false only after those commands failed, not because you think you lack tools.\n";
    s += "Create and checkout feature/leftover-raw-develop from origin/main if needed.\n";
    s += "Read with tools: AGENTS.md, develop_plan.md section 1.1, implement_goals.md living pointer, docs/desktop_development_plan.md section 5.6 and 10, docs/v2_known_limitations.md Deferred Formats, docs/api.md RAW paragraph, ";
    s += "apps/api/app/image/raw_preview.py, apps/api/app/services/importing.py (expand_import_paths RAW probe, register_import_file, import_image_file, _open_imported_image), ";
    s += "apps/api/tests/test_raw_preview.py, apps/api/tests/raw_helpers.py, apps/api/tests/test_import_path_expansion.py, apps/api/tests/test_import_from_paths.py, apps/api/tests/test_import_process_export_api.py RAW skip tests.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: leftover plan for RAW fallback develop', do not redo. Return ok=true with that SHA.\n";
    s += "GitHub issue: first run gh issue list --repo joe-cheung-cae/frame-pilot --state open and --state all --limit 30. Search for an existing leftover RAW fallback / demosaic issue. If none, create ONE with gh issue create --repo joe-cheung-cae/frame-pilot, or GitHub MCP after search_tool. ";
    s += "Title exactly: Leftover: RAW fallback develop (no embedded preview). ";
    s += "Body must say: S9.04 #162 shipped extract_thumb only; this leftover is fallback LibRaw postprocess when no embedded preview; not a RAW editor; not Phase 10; originals unchanged; expand_import_paths must not postprocess; extra RAW extensions out; color-managed develop remains unscheduled. Use the number GitHub returns. Write owner/repo#N in the plan. Do not guess the number before create. Do not invent issue numbers from other repos or Mem.\n";
    s += "Write bilingual leftover plan docs/plans/2026-09-11-leftover-raw-develop.md and docs/plans/2026-09-11-leftover-raw-develop.zh.md. Each English page links to the Chinese counterpart near the top and vice versa. Include: why leftover not Phase 10; locked decisions from this prompt; status board with 需求拆解/评审/归档/开发/测试/上线; file map; test inversion table; non-goals.\n";
    s += "Status board: tick 需求拆解 [x] in this commit only. Leave 开发 and 上线 [ ].\n";
    s += "Update develop_plan.md section 1.1 (+ zh) Next to this leftover (name the issue). Remaining unscheduled: auto-download/install, processing pool, color-managed RAW / extra extensions, SmartScreen/store listing. Do not invent Phase 10.\n";
    s += "Update docs/desktop_development_plan.md section 5.6 (+ zh): split Full RAW develop into this leftover [ ] fallback demosaic vs color-managed still deferred (unscheduled). Section 10 Unscheduled must not call this leftover Phase 10.\n";
    s += "Point implement_goals.md (+ zh) living pointer at section 1.1 leftover; still say do not invent Phase 10.\n";
    s += "If .grok/workflows/leftover-raw-develop.rhai exists, include it in this commit.\n";
    s += "Commit subject exactly: docs: leftover plan for RAW fallback develop\n";
    s += "If nothing is staged, skip an empty commit.\n";
    s += github_tail();
    s += "Return ok=true, stage=需求拆解, commit=full sha, handoff=docs/plans/2026-09-11-leftover-raw-develop.md, notes=issue number, PR URL, contract summary.\n";
    s
}

fn review_prompt() {
    let s = "";
    s += "You are the 评审 agent for FramePilot leftover RAW fallback develop. Adversarially review the leftover plan against the live tree. Do not implement production Python yet.\n";
    s += repo_rules();
    s += "You have git and gh. Stay on feature/leftover-raw-develop. Commit and push if you change the bilingual plan or living pointers; otherwise skip an empty commit and still return ok=true.\n";
    s += "Read the leftover plan (+ zh), develop_plan.md section 1.1, docs/desktop_development_plan.md section 5.6, raw_preview.py, importing.py RAW call sites, test_raw_preview.py, raw_helpers.py tiny_dng_without_preview_bytes, packaging/pyinstaller/framepilot-api.spec for rawpy collect.\n";
    s += "Confirm ALL: (1) leftover not Phase 10; (2) extract_raw_preview_image stays thumb-only; (3) expand_import_paths will not postprocess; (4) skip reason changes only when both paths fail; (5) tiny DNG without preview is the positive fixture; (6) issue number in the plan matches gh; (7) section 1.1 Next names this leftover; (8) PyInstaller already collects rawpy or the plan says how 评审 confirmed no extra hiddenimports.\n";
    s += "Fix bilingual plan holes only if the live tree makes the spec wrong. Do not tick 开发 or 上线.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: review leftover RAW fallback develop', do not redo. Return ok=true with that SHA.\n";
    s += "Commit subject exactly: docs: review leftover RAW fallback develop\n";
    s += "If nothing is staged, skip an empty commit and still return ok=true.\n";
    s += github_tail();
    s += "Return ok=true, stage=评审, commit=HEAD sha, handoff=docs/plans/2026-09-11-leftover-raw-develop.md, notes=review summary.\n";
    s
}

fn skeptic_prompt() {
    let s = "";
    s += "You are a read-only skeptic for leftover RAW fallback develop. Use grep/read_file/gh. Do not edit.\n";
    s += "Confirm with evidence (file:line or issue URL) ALL of: ";
    s += "(1) develop_plan.md section 1.1 Next names this leftover and does not invent Phase 10; ";
    s += "(2) apps/api/app/image/raw_preview.py extract_raw_preview_image still never calls postprocess on origin/main (or this branch if already implemented, still never when thumb succeeds); ";
    s += "(3) expand_import_paths currently probes extract_thumb on the sync path — the leftover plan forbids moving postprocess there; ";
    s += "(4) originals must stay byte-identical; ";
    s += "(5) tiny_dng_without_preview_bytes exists in apps/api/tests/raw_helpers.py; ";
    s += "(6) extra RAW extensions remain out of SUPPORTED_EXTENSIONS; ";
    s += "(7) this leftover is the right next slice and must not be called Phase 10.\n";
    s += "Set real=true only with evidence you independently read. Set ok=true if this leftover is still the right next slice. notes=short. evidence=file:line citations.\n";
    s
}

fn archive_prompt() {
    let s = "";
    s += "You are the 归档 agent for FramePilot leftover RAW fallback develop. Do not implement production Python yet.\n";
    s += repo_rules();
    s += "Read docs/plans/2026-09-11-leftover-raw-develop.md status board. 开发 must still be [ ] unless subject 'feat: demosaic RAW without embedded preview' already exists (idempotent).\n";
    s += "Record that 开发 MUST: tests first; open_raw_import_image thumb-then-postprocess; invert skip tests; tick leftover-plan 开发 [x] in that same commit; push; must NOT tick 上线 or claim color-managed RAW.\n";
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'docs: archive leftover RAW fallback develop', do not redo. Return ok=true with that SHA.\n";
    s += "Commit subject exactly: docs: archive leftover RAW fallback develop\n";
    s += "If nothing is staged, skip an empty commit and return ok=true.\n";
    s += github_tail();
    s += "Return ok=true, stage=归档, commit=HEAD sha, handoff=docs/plans/2026-09-11-leftover-raw-develop.md, notes=ready for 开发.\n";
    s
}

fn develop_prompt() {
    let s = "";
    s += "You are the 开发 agent for FramePilot leftover RAW fallback develop. Tests first, then minimal implementation. Do not start 上线 living-docs close-out. Do not dispatch desktop.yml.\n";
    s += repo_rules();
    s += "IDEMPOTENT: if git log origin/main..HEAD already contains subject 'feat: demosaic RAW without embedded preview', do not redo implementation. Return ok=true with that SHA.\n";
    s += "TESTS FIRST. Invert/add tests so they fail for the right reason, then implement.\n";
    s += "Keep extract_raw_preview_image thumb-only. Watch test_extract_raw_preview_does_not_call_postprocess stay red if you accidentally call postprocess on preview DNG — that test must remain green after the change.\n";
    s += "Add tests in apps/api/tests/test_raw_preview.py: tiny_dng_without_preview_bytes opens via open_raw_import_image, tracking wrapper shows extract_thumb then postprocess, returns RGB, source bytes unchanged. Preview DNG tracking through open_raw_import_image is extract_thumb only. Garbage bytes raise the new develop-failed reason.\n";
    s += "Invert expansion tests: empty/garbage/no-preview DNG must be collected by expand_import_paths (do not skip at expansion). Failure happens at register/import job with cleanup.\n";
    s += "Invert import/process/export tests that currently skip tiny_dng_without_preview_bytes: copy original, WebP derivatives, score, export original bytes ZIP_STORED. Garbage still skip/fail with new reason and no originals leftover.\n";
    s += "Implement open_raw_import_image in apps/api/app/image/raw_preview.py (name may match the leftover plan). Call it from _open_imported_image, register_import_file RAW probe, and any other import open of RAW. Remove the expansion-time skip-on-RawPreviewError so RAW suffixes collect.\n";
    s += "Before postprocess, honor import cancel: in _run_one_import_derivative_task / process_registered_import_photo, if the job is cancellation_requested do not start postprocess. Use existing _import_job_cancellation_requested; do not add Redis.\n";
    s += "Tick leftover plan 开发 [x] (en+zh) in the SAME commit. Do not tick 上线. Do not rewrite every living doc yet (上线 does that) unless a user-facing Python string requires a one-line doc note.\n";
    s += "Run: pytest apps/api/tests/test_raw_preview.py apps/api/tests/test_import_path_expansion.py apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_process_export_api.py -q --tb=short (or the subset that covers RAW). Then npm run lint:api if you touched Python.\n";
    s += "Commit subject exactly: feat: demosaic RAW without embedded preview\n";
    s += "Include tests, implementation, and leftover plan 开发 ticks in that commit.\n";
    s += github_tail();
    s += "Return ok=true only if the named tests passed and the commit exists. stage=开发, commit=full sha, handoff=docs/plans/2026-09-11-leftover-raw-develop.md, notes=summary including PR URL.\n";
    s
}

fn test_prompt() {
    let s = "";
    s += "You are the 测试 agent for FramePilot leftover RAW fallback develop. Fail closed. Re-run tests yourself. Do not start 上线 docs. Do not dispatch desktop.yml.\n";
    s += repo_rules();
    s += "1) git log origin/main..HEAD --format='%s' must contain 'feat: demosaic RAW without embedded preview'.\n";
    s += "2) Re-run pytest apps/api/tests/test_raw_preview.py apps/api/tests/test_import_path_expansion.py apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_process_export_api.py -q --tb=short. Re-run npm run lint:api.\n";
    s += "3) Confirm tracking tests: preview DNG never postprocess; no-preview DNG does postprocess; garbage uses the new reason; originals bytes unchanged.\n";
    s += "4) git diff origin/main...HEAD --stat must stay inside this leftover file map: leftover plan md+zh, raw_preview.py, importing.py, named tests, raw_helpers if needed, .grok/workflows/leftover-raw-develop.rhai, bilingual living pointers from 需求拆解. No original photos, certs, or model weights.\n";
    s += "5) Confirm docs/plans/2026-09-11-leftover-raw-develop.md 上线 is still [ ] on this branch.\n";
    s += "Set passed=true only if you ran the checks and they succeeded. ok=true only if passed=true and scope is clean.\n";
    s += "If tests fail, fix only this leftover's files, keep one logical develop commit (amend only if HEAD is the develop commit and not yet depended on), re-run.\n";
    s += "Return stage=测试, commit=HEAD sha, handoff=docs/plans/2026-09-11-leftover-raw-develop.md, notes=commands and results.\n";
    s
}

fn launch_prompt() {
    let s = "";
    s += "You are the 上线 agent for FramePilot leftover RAW fallback develop. Do not merge to main. Do not invent Phase 10. Do not dispatch desktop.yml.\n";
    s += repo_rules();
    s += "Confirm git status clean except untracked noise. Confirm push happened. Confirm the single draft PR exists (create if missing).\n";
    s += "Read the leftover plan for the GitHub issue number.\n";
    s += "GREEN path: named tests already passed in 测试. Then commit subject exactly: docs: record leftover RAW fallback develop\n";
    s += "That evidence commit MUST update bilingual living docs to match shipped fallback demosaic: ";
    s += "docs/v2_known_limitations.md Deferred Formats; docs/api.md RAW paragraph; docs/architecture.md import RAW sentence; docs/v2_algorithm_strategy.md; README.md formats; CHANGELOG Unreleased; implement_goals.md pointer; ";
    s += "docs/desktop_development_plan.md section 5.6 leftover fallback row [x] and color-managed still unscheduled; section 10 Unscheduled without calling this Phase 10; ";
    s += "develop_plan.md section 1.1: leftover shipped on this branch, Next has no further named leftover, remaining unscheduled are auto-download/install, processing pool, color-managed RAW / extra extensions, SmartScreen/store listing; ";
    s += "leftover plan 上线 [x] and 测试 [x] if not already. Use ISO-8601 timestamps with timezone (UTC Z is fine) when you record time. Do not bump APP_VERSION.\n";
    s += "Keep the draft PR body as Refs the leftover issue. Do not say Fixes or Close. Do not merge.\n";
    s += "After the evidence commit, git push -u origin HEAD and comment the leftover issue with leftover RAW fallback develop, full SHA, pytest commands, and PR URL. Do not close the issue.\n";
    s += "RED path: if 测试 did not pass, do NOT tick 上线. Comment the leftover issue with the failure. Set ok=false. notes must say leftover not claimed.\n";
    s += "Return ok=true only if the evidence commit exists AND living docs match fallback demosaic AND the issue comment was posted. stage=上线, commit=full sha, handoff=docs/plans/2026-09-11-leftover-raw-develop.md, notes=PR URL and comment.\n";
    s
}

phase("Inspect");
log("Inspect leftover RAW fallback develop progress");
let progress = agent(inspect_prompt(), inspect_opts("leftover-raw-develop-inspect"));
if !stage_ok(progress) {
    await_user("verification", "Inspect failed. Resume to retry Inspect. Do not skip to 需求拆解.");
    progress = agent(inspect_prompt(), inspect_opts("leftover-raw-develop-inspect"));
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
        task: "leftover-raw-develop",
        notes: "All stages already committed; nothing to run.",
    });
}

let breakdown_r = ();
if run_breakdown {
    phase("需求拆解");
    log("Leftover RAW fallback develop 需求拆解");
    breakdown_r = run_stage(breakdown_prompt(), plan_opts("leftover-raw-develop-breakdown"), "需求拆解 failed; inspect before 评审.");
} else {
    log("Skipping 需求拆解 (already committed)");
}

if run_review {
    phase("评审");
    log("Leftover RAW fallback develop 评审");
    run_stage(review_prompt(), plan_opts("leftover-raw-develop-review"), "评审 failed; inspect before 归档.");
    let sk = agent(skeptic_prompt(), skeptic_opts("leftover-raw-develop-skeptic"));
    if !stage_ok(sk) {
        await_user("verification", "Skeptic agent failed. Resume to retry 评审. Do not skip to 开发.");
        sk = agent(skeptic_prompt(), skeptic_opts("leftover-raw-develop-skeptic"));
    }
    if stage_ok(sk) && sk.output != () && sk.output.real == false {
        await_user("verification", "Skeptic set real=false. Resume only after the contract matches live code.");
    }
} else {
    log("Skipping 评审 (already committed)");
}

if run_archive {
    phase("归档");
    log("Leftover RAW fallback develop 归档");
    run_stage(archive_prompt(), agent_opts("leftover-raw-develop-archive"), "归档 failed; inspect before 开发.");
} else {
    log("Skipping 归档 (already committed)");
}

if run_develop {
    phase("开发");
    log("Leftover RAW fallback develop 开发");
    run_stage(develop_prompt(), agent_opts("leftover-raw-develop-develop"), "开发 failed; inspect before 测试. Do not skip the GitHub push.");
} else {
    log("Skipping 开发 (already committed)");
}

if run_test {
    phase("测试");
    log("Leftover RAW fallback develop 测试");
    let test_r = run_stage(test_prompt(), test_opts("leftover-raw-develop-test"), "测试 failed; do not 上线.");
    if !declared_passed(test_r) {
        await_user("verification", "Tests did not pass. Resume to retry 测试. Do not 上线.");
    }
} else {
    log("Skipping 测试 (already verified)");
}

let launch_r = ();
if run_launch {
    phase("上线");
    log("Leftover RAW fallback develop 上线 — living docs and issue comment; do not merge");
    launch_r = run_stage(launch_prompt(), agent_opts("leftover-raw-develop-launch"), "上线 failed; inspect git push, draft PR, and issue comment. Do not merge.");
} else {
    log("Skipping 上线 (evidence commit already present)");
}

complete(#{
    ok: if run_launch { stage_ok(launch_r) && declared_ok(launch_r) } else { true },
    task: "leftover-raw-develop",
    commit: if launch_r != () && launch_r.output != () { launch_r.output.commit } else { "" },
    notes: if launch_r != () && launch_r.output != () { launch_r.output.notes } else { "leftover-raw-develop workflow finished" },
});
