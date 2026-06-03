import test from "node:test";
import assert from "node:assert/strict";

import {
  countPhotosByStatus,
  EXPORT_STATUSES,
  formatExportStatusSummary,
  isExportDownloadable,
  selectedPhotoCount,
  type ExportStatus,
} from "./exportSelection.ts";

test("counts photos by export status", () => {
  const counts = countPhotosByStatus([
    { user_status: "Pick" },
    { user_status: "Pick" },
    { user_status: "Maybe" },
    { user_status: "Reject" },
  ]);

  assert.deepEqual(counts, { Pick: 2, Maybe: 1, Reject: 1, Unreviewed: 0 });
});

test("sums selected export statuses", () => {
  const counts: Record<ExportStatus, number> = { Pick: 3, Maybe: 2, Reject: 1, Unreviewed: 5 };

  assert.equal(selectedPhotoCount(counts, ["Pick", "Maybe"]), 5);
  assert.equal(selectedPhotoCount(counts, []), 0);
});

test("keeps the supported status order stable", () => {
  assert.deepEqual(EXPORT_STATUSES, ["Pick", "Maybe", "Reject", "Unreviewed"]);
});

test("formats export status summaries from stored JSON", () => {
  assert.equal(formatExportStatusSummary('["Maybe","Pick"]'), "Pick, Maybe");
  assert.equal(formatExportStatusSummary("[]"), "No statuses");
  assert.equal(formatExportStatusSummary("not json"), "Unknown statuses");
});

test("allows downloads only for completed file exports", () => {
  assert.equal(isExportDownloadable({ mode: "csv", status: "complete" }), true);
  assert.equal(isExportDownloadable({ mode: "zip", status: "complete" }), true);
  assert.equal(isExportDownloadable({ mode: "folder", status: "complete" }), false);
  assert.equal(isExportDownloadable({ mode: "csv", status: "failed" }), false);
  assert.equal(isExportDownloadable({ mode: "zip", status: "running" }), false);
});
