# Desktop Phase 2 code-review round 1

Handoff stage: `Handoff` (Review round 1)  
Date: 2026-08-21T11:14:05+08:00  
Branch: `feature/desktop-phase2`  
Live HEAD: `95e03fb39b0e04e44024e2367b2ab974f0a43e5d` (`test: verify small folder path import is not duplicated`)  
Base: `origin/main` `69f41bcfb35948c9921e10a41ffd0f505ba49dad`  
PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (do not merge)

This is the round-1 record of the Phase 2 implementation review against **current HEAD**. The filed defects are in `docs/handoff/phase2-code-review-findings.md` (Issue 1 bug, Issue 2 suggestion). Confirmed findings for this round were re-checked against live source; no extras were added.

**Gating bugs this round: 0.** Phase 2 is merge-gating clean for this round.

---

## Counts

| Class | Count |
|-------|-------|
| bugs | 0 |
| suggestions | 0 |
| nits | 0 |
| confirmed findings | 0 |

Confirmed findings JSON: `[]`.

---

## Issue 1 / Issue 2 status

### Issue 1 — small-folder path import duplication — **fixed**

Filed against `apps/web/src/lib/api.ts` (~428): a directory first slice used `finalize: false`; when `remaining_paths` was empty the client re-POSTed the **same folder** with `finalize: true`, and `POST /imports/from-paths` re-expanded and re-registered copies (`hero-1.jpg`, `alt-1.jpg`).

Evidence on HEAD `95e03fb39b0e04e44024e2367b2ab974f0a43e5d`:

- Product fix: `67505aa7ede3249d85f82e5b39920975fee17f1f` `fix: stop duplicating photos on small folder path import`.
- Client (`apps/web/src/lib/api.ts:425-432`): after `remaining_paths` is empty and the first slice was not last, the follow-up is `importPhotosFromPathsBatch(projectId, [], { jobId, expectedTotal, finalize: true })` — empty `paths`, not the folder.
- API (`apps/api/app/api/routes.py:584-589`): empty `paths` is a finalize-only follow-up; it does not call `expand_import_paths` and requires `finalize` plus `job_id`.
- Live TestClient sequence (`apps/api/tests/test_import_from_paths.py:146-187` `test_import_from_paths_small_folder_finalize_only_follow_up_keeps_two_originals`): folder with `hero.jpg` + `alt.jpg`, first POST `finalize: false`, second POST `paths: []` / `finalize: true` → `total_images == 2`, originals only `alt.jpg` / `hero.jpg`. Sources unchanged.

### Issue 2 — unit test encoded the duplicating protocol — **fixed**

Filed against `apps/web/src/lib/importWorkflow.test.ts:347`: the mock required a second request with `paths: [folder]`.

Evidence on HEAD:

- Same test (`importWorkflow.test.ts:347-377`) still requires two requests, but the second body is `finalize: true`, `job_id: "job-1"`, `expected_total: 2`, and **`paths: []`** (`assert.deepEqual(calls[1]?.paths, [])`).
- That matches the shipped client loop and the API finalize-only follow-up. It no longer locks in re-POSTing the folder.

---

## Confirmed findings (this round)

None. Empty list is valid: Issue 1 and Issue 2 are fixed on HEAD, and no additional gating bugs, suggestions, or nits were confirmed.

---

## Verdict

**bugs = 0.** Phase 2 is merge-gating clean for this round.

Next stage: Close-out (not Repair). Do not start Phase 3–5. Do not bump `APP_VERSION`. Do not merge PR 38.
