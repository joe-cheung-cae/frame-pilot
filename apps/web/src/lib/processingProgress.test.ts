import test from "node:test";
import assert from "node:assert/strict";

import {
  activeJobOfType,
  activeProcessingJob,
  hasActiveProcessingJob,
  processingActionBlockMessage,
  processingFailureNotice,
  processingJobTypeLabel,
  processingLoadRecoveryMessage,
  processingProgressPercent,
  processingProgressSummary,
  processingRecoveryMessage,
  processingStatusLabel,
} from "./processingProgress.ts";

test("formats processing status labels", () => {
  assert.equal(processingStatusLabel(undefined), "Ready");
  assert.equal(processingStatusLabel("running"), "Running");
  assert.equal(processingStatusLabel("complete_with_errors"), "Complete with errors");
  assert.equal(processingStatusLabel("cancelled"), "Cancelled");
  assert.equal(processingStatusLabel("failed"), "Failed");
});

test("formats processing job type labels", () => {
  assert.equal(processingJobTypeLabel("import"), "Import");
  assert.equal(processingJobTypeLabel("processing"), "Grouping and ranking");
  assert.equal(processingJobTypeLabel("export"), "Export");
  assert.equal(processingJobTypeLabel("metadata"), "Metadata");
  assert.equal(processingJobTypeLabel(""), "Job");
});

test("detects active processing jobs", () => {
  assert.equal(hasActiveProcessingJob(undefined), false);
  assert.equal(
    hasActiveProcessingJob([
      { job_type: "processing", status: "complete" },
      { job_type: "import", status: "failed" },
    ]),
    false,
  );
  assert.equal(
    hasActiveProcessingJob([
      { job_type: "processing", status: "complete" },
      { job_type: "import", status: "running" },
    ]),
    true,
  );
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

test("formats active job progress without noisy zero-failure counts", () => {
  assert.equal(
    processingProgressSummary(
      {
        failed_items: 0,
        job_type: "processing",
        processed_items: 8,
        progress_percent: 83.2,
        status: "running",
        total_items: 12,
      },
      { processed_images: 0, total_images: 12 },
    ),
    "8 of 12 photos · 83%",
  );
});

test("formats singular active job progress nouns", () => {
  assert.equal(
    processingProgressSummary(
      {
        failed_items: 0,
        job_type: "import",
        processed_items: 1,
        progress_percent: 100,
        status: "complete",
        total_items: 1,
      },
      { processed_images: 0, total_images: 1 },
    ),
    "1 of 1 file · 100%",
  );
  assert.equal(
    processingProgressSummary(
      {
        failed_items: 1,
        job_type: "processing",
        processed_items: 1,
        progress_percent: 50,
        status: "running",
        total_items: 1,
      },
      { processed_images: 0, total_images: 1 },
    ),
    "1 of 1 photo · 1 failed · 50%",
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

test("explains processing recovery for failed jobs", () => {
  assert.equal(
    processingRecoveryMessage({ failedItems: 0, retryable: true, status: "failed" }),
    "Retry will rebuild local grouping and ranking metadata without modifying original files.",
  );
  assert.equal(
    processingRecoveryMessage({ failedItems: 0, retryable: false, status: "failed" }),
    "Imported files remain safe. Reimport affected images or resolve failed local files before running again.",
  );
});

test("explains processing recovery for cancelled and partial jobs", () => {
  assert.equal(
    processingRecoveryMessage({ failedItems: 0, retryable: true, status: "cancelled" }),
    "Processing stopped at a safe checkpoint. Run grouping and ranking again when you are ready.",
  );
  assert.equal(
    processingRecoveryMessage({ failedItems: 2, retryable: true, status: "complete_with_errors" }),
    "Successfully processed photos are ready for culling. Review failed photos before exporting a final set.",
  );
});

test("omits processing recovery when no recovery guidance is needed", () => {
  assert.equal(processingRecoveryMessage({ failedItems: 0, retryable: true, status: "complete" }), "");
  assert.equal(processingRecoveryMessage({ failedItems: 0, retryable: true, status: "complete_with_errors" }), "");
  assert.equal(processingRecoveryMessage({ failedItems: 0, retryable: false, status: null }), "");
});

test("explains how to recover from processing data load failures", () => {
  assert.equal(
    processingLoadRecoveryMessage("project"),
    "Confirm the local FramePilot API is running, then reload this processing page. Imported originals remain unchanged.",
  );
  assert.equal(
    processingLoadRecoveryMessage("job"),
    "Confirm the local FramePilot API is running, then reload processing status. Existing local job records remain in the project database.",
  );
  assert.equal(
    processingLoadRecoveryMessage("history"),
    "Confirm the local FramePilot API is running, then reload job history. Project data stays on this computer.",
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
