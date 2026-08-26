import test from "node:test";
import assert from "node:assert/strict";

import { jobLabel, projectLabel, resolveStatusBarProjectId, sidecarLabel, statusBarJob } from "./statusBarModel.ts";

test("labels sidecar connection states in English", () => {
  assert.equal(sidecarLabel(true), "Sidecar connected");
  assert.equal(sidecarLabel(false), "Sidecar disconnected");
  assert.equal(sidecarLabel(null), "Checking sidecar");
});

test("labels the current project or No project", () => {
  assert.equal(projectLabel("Coast shoot"), "Coast shoot");
  assert.equal(projectLabel("  "), "No project");
  assert.equal(projectLabel(null), "No project");
  assert.equal(projectLabel(undefined), "No project");
});

test("resolves the status-bar project id from the path then last opened", () => {
  assert.equal(resolveStatusBarProjectId("/projects/abc/cull", "fallback"), "abc");
  assert.equal(resolveStatusBarProjectId("/projects/new", "fallback"), "fallback");
  assert.equal(resolveStatusBarProjectId("/help", "fallback"), "fallback");
  assert.equal(resolveStatusBarProjectId("/projects/new", null), null);
  assert.equal(resolveStatusBarProjectId("/", "  "), null);
});

test("formats an idle job as No active job", () => {
  assert.equal(jobLabel(undefined), "No active job");
  assert.equal(jobLabel(null), "No active job");
});

test("formats job type, step, and clamped percent from processingProgress helpers", () => {
  assert.equal(
    jobLabel({
      job_type: "processing",
      status: "running",
      current_step: "Building groups",
      progress_percent: 42.4,
    }),
    "Grouping and ranking · Building groups · 42%",
  );
  assert.equal(
    jobLabel({
      job_type: "import",
      status: "running",
      current_step: "  ",
      progress_percent: 130,
    }),
    "Import · Running · 100%",
  );
});

test("prefers an active job of any type over a completed processing job", () => {
  const jobs = [
    {
      id: "done",
      job_type: "processing",
      status: "complete" as const,
    },
    {
      id: "importing",
      job_type: "import",
      status: "running" as const,
    },
  ];
  assert.equal(statusBarJob(jobs)?.id, "importing");
  assert.equal(statusBarJob(undefined), undefined);
  assert.equal(statusBarJob(jobs.slice(0, 1))?.id, "done");
});
