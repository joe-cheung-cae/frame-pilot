import test from "node:test";
import assert from "node:assert/strict";

import { projectNextActionLabel, projectNextHref, projectProgressSummary } from "./projectRouting.ts";

test("routes empty projects to import", () => {
  assert.equal(
    projectNextHref({ id: "p1", total_images: 0, processed_images: 0, active_import_job: null }),
    "/projects/p1/import",
  );
});

test("routes imported but unprocessed projects to processing", () => {
  assert.equal(
    projectNextHref({ id: "p1", total_images: 3, processed_images: 0, active_import_job: null }),
    "/projects/p1/process",
  );
});

test("routes processed projects to culling", () => {
  assert.equal(
    projectNextHref({ id: "p1", total_images: 3, processed_images: 3, active_import_job: null }),
    "/projects/p1/cull",
  );
});

test("routes active import projects back to import progress", () => {
  assert.equal(
    projectNextHref({
      id: "p1",
      total_images: 3,
      processed_images: 3,
      active_import_job: { status: "running" },
    }),
    "/projects/p1/import",
  );
  assert.equal(
    projectNextActionLabel({
      total_images: 3,
      processed_images: 0,
      active_import_job: { status: "queued" },
    }),
    "Import in progress",
  );
});

test("labels the next resumable project step", () => {
  assert.equal(projectNextActionLabel({ total_images: 0, processed_images: 0, active_import_job: null }), "Import images");
  assert.equal(
    projectNextActionLabel({ total_images: 3, processed_images: 0, active_import_job: null }),
    "Process photos",
  );
  assert.equal(
    projectNextActionLabel({ total_images: 3, processed_images: 1, active_import_job: null }),
    "Continue culling",
  );
  assert.equal(
    projectNextActionLabel({ total_images: 3, processed_images: 3, active_import_job: null }),
    "Review culling",
  );
});

test("summarizes project progress by workflow stage", () => {
  assert.equal(
    projectProgressSummary({ total_images: 0, processed_images: 0, active_import_job: null }),
    "No photos imported yet",
  );
  assert.equal(
    projectProgressSummary({ total_images: 1, processed_images: 0, active_import_job: { status: "running" } }),
    "1 photo registered; import still running",
  );
  assert.equal(
    projectProgressSummary({ total_images: 3, processed_images: 0, active_import_job: null }),
    "3 photos imported; processing not started",
  );
  assert.equal(
    projectProgressSummary({ total_images: 3, processed_images: 2, active_import_job: null }),
    "2 of 3 photos processed",
  );
});
