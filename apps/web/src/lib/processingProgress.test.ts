import test from "node:test";
import assert from "node:assert/strict";

import {
  activeJobOfType,
  activeProcessingJob,
  processingActionBlockMessage,
  processingFailureNotice,
  processingProgressPercent,
  processingProgressSummary,
  processingStatusLabel,
} from "./processingProgress.ts";

test("formats processing status labels", () => {
  assert.equal(processingStatusLabel(undefined), "Ready");
  assert.equal(processingStatusLabel("running"), "Running");
  assert.equal(processingStatusLabel("complete_with_errors"), "Complete with errors");
  assert.equal(processingStatusLabel("cancelled"), "Cancelled");
  assert.equal(processingStatusLabel("failed"), "Failed");
});

test("clamps processing progress percentages", () => {
  assert.equal(processingProgressPercent(undefined), 0);
  assert.equal(processingProgressPercent({ progress_percent: 42.6 }), 43);
  assert.equal(processingProgressPercent({ progress_percent: -10 }), 0);
  assert.equal(processingProgressPercent({ progress_percent: 130 }), 100);
});

test("formats project progress before a job starts", () => {
  assert.equal(processingProgressSummary(undefined, { processed_images: 3, total_images: 10 }), "3 of 10 processed");
  assert.equal(processingProgressSummary(undefined, undefined), "0 of 0 processed");
});

test("formats active job progress with failed item counts", () => {
  assert.equal(
    processingProgressSummary(
      {
        failed_items: 2,
        job_type: "processing",
        processed_items: 8,
        progress_percent: 83.2,
        status: "running",
        total_items: 12,
      },
      { processed_images: 0, total_images: 12 },
    ),
    "8 of 12 photos · 2 failed · 83%",
  );
});

test("formats processing failure notices", () => {
  assert.equal(processingFailureNotice(undefined), null);
  assert.equal(processingFailureNotice({ error_message: null, failed_items: 0, job_type: "processing" }), null);
  assert.equal(
    processingFailureNotice({
      error_message: "1 photo could not be processed during scoring.",
      failed_items: 1,
      job_type: "processing",
    }),
    "1 photo could not be processed during scoring.",
  );
  assert.equal(
    processingFailureNotice({ error_message: null, failed_items: 2, job_type: "processing" }),
    "2 photos could not be processed.",
  );
  assert.equal(
    processingFailureNotice({ error_message: null, failed_items: 1, job_type: "import" }),
    "1 file could not be imported.",
  );
});

test("explains why processing action is blocked", () => {
  assert.equal(
    processingActionBlockMessage({ hasImportedPhotos: true, isImportRunning: false, isProcessing: true }),
    "Grouping and ranking is already running.",
  );
  assert.equal(
    processingActionBlockMessage({ hasImportedPhotos: true, isImportRunning: true, isProcessing: false }),
    "Wait for import previews and analysis to finish before processing.",
  );
  assert.equal(
    processingActionBlockMessage({ hasImportedPhotos: false, isImportRunning: false, isProcessing: false }),
    "Import JPEG, PNG, or WebP images before running grouping and ranking.",
  );
});

test("allows processing action when imports are ready", () => {
  assert.equal(
    processingActionBlockMessage({ hasImportedPhotos: true, isImportRunning: false, isProcessing: false }),
    "",
  );
});

test("selects the newest active processing job from ordered jobs", () => {
  const active = { id: "job-2", job_type: "processing", status: "running" as const };
  const jobs = [
    { id: "job-3", job_type: "processing", status: "failed" as const },
    active,
    { id: "job-1", job_type: "processing", status: "queued" as const },
  ];

  assert.equal(activeProcessingJob(jobs), active);
  assert.equal(
    activeProcessingJob([{ id: "export-1", job_type: "export", status: "running" as const }]),
    undefined,
  );
  assert.equal(activeProcessingJob(undefined), undefined);
});

test("selects the newest active job by type from ordered jobs", () => {
  const activeImport = { id: "job-2", job_type: "import", status: "running" as const };
  const jobs = [
    { id: "job-3", job_type: "processing", status: "running" as const },
    activeImport,
    { id: "job-1", job_type: "import", status: "queued" as const },
  ];

  assert.equal(activeJobOfType(jobs, "import"), activeImport);
  assert.equal(activeJobOfType(jobs, "export"), undefined);
});
