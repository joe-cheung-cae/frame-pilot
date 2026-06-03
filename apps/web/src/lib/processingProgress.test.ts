import test from "node:test";
import assert from "node:assert/strict";

import {
  processingProgressPercent,
  processingProgressSummary,
  processingStatusLabel,
} from "./processingProgress.ts";

test("formats processing status labels", () => {
  assert.equal(processingStatusLabel(undefined), "Ready");
  assert.equal(processingStatusLabel("running"), "Running");
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
