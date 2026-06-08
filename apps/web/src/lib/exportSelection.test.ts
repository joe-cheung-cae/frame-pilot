import test from "node:test";
import assert from "node:assert/strict";

import {
  applyStatusCountChange,
  countPhotosByStatus,
  EXPORT_STATUSES,
  exportActionBlockMessage,
  exportRecoveryMessage,
  exportSelectedCountLabel,
  exportStatusCountLabel,
  formatExportRecordStatus,
  formatExportStatusSummary,
  hasRunningExport,
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

test("formats selected export counts without showing fallback zeros while loading", () => {
  assert.equal(exportSelectedCountLabel({ isLoading: true, selectedCount: 0 }), "Loading selected photos");
  assert.equal(exportSelectedCountLabel({ isLoading: false, selectedCount: 1 }), "1 photo selected");
  assert.equal(exportSelectedCountLabel({ isLoading: false, selectedCount: 2 }), "2 photos selected");
});

test("formats status counts without showing fallback zeros while loading", () => {
  assert.equal(exportStatusCountLabel({ count: 0, isLoading: true }), "Loading");
  assert.equal(exportStatusCountLabel({ count: 4, isLoading: false }), "4");
});

test("explains why export action is blocked", () => {
  assert.equal(
    exportActionBlockMessage({
      isExporting: true,
      isStatusCountsLoading: false,
      selectedCount: 2,
      selectedStatuses: ["Pick"],
    }),
    "Export is running. Wait for it to finish before changing export settings.",
  );
  assert.equal(
    exportActionBlockMessage({
      isExporting: false,
      isStatusCountsLoading: true,
      selectedCount: 0,
      selectedStatuses: ["Pick"],
    }),
    "Loading photo status counts before export.",
  );
  assert.equal(
    exportActionBlockMessage({
      isExporting: false,
      isStatusCountsLoading: false,
      selectedCount: 0,
      selectedStatuses: [],
    }),
    "Choose at least one status to export.",
  );
  assert.equal(
    exportActionBlockMessage({
      isExporting: false,
      isStatusCountsLoading: false,
      selectedCount: 0,
      selectedStatuses: ["Pick"],
    }),
    "No photos match the selected statuses.",
  );
});

test("allows export action when settings select photos", () => {
  assert.equal(
    exportActionBlockMessage({
      isExporting: false,
      isStatusCountsLoading: false,
      selectedCount: 1,
      selectedStatuses: ["Pick"],
    }),
    "",
  );
});

test("moves status counts when a photo status changes", () => {
  const counts: Record<ExportStatus, number> = { Pick: 1, Maybe: 0, Reject: 0, Unreviewed: 3 };

  assert.deepEqual(applyStatusCountChange(counts, "Unreviewed", "Pick"), {
    Pick: 2,
    Maybe: 0,
    Reject: 0,
    Unreviewed: 2,
  });
  assert.deepEqual(counts, { Pick: 1, Maybe: 0, Reject: 0, Unreviewed: 3 });
});

test("keeps status count changes non-negative and handles no-op transitions", () => {
  const counts: Record<ExportStatus, number> = { Pick: 0, Maybe: 1, Reject: 0, Unreviewed: 0 };

  assert.deepEqual(applyStatusCountChange(counts, "Pick", "Reject"), {
    Pick: 0,
    Maybe: 1,
    Reject: 1,
    Unreviewed: 0,
  });
  assert.deepEqual(applyStatusCountChange(counts, "Maybe", "Maybe"), counts);
});

test("keeps the supported status order stable", () => {
  assert.deepEqual(EXPORT_STATUSES, ["Pick", "Maybe", "Reject", "Unreviewed"]);
});

test("formats export status summaries from stored JSON", () => {
  assert.equal(formatExportStatusSummary('["Maybe","Pick"]'), "Pick, Maybe");
  assert.equal(formatExportStatusSummary("[]"), "No statuses");
  assert.equal(formatExportStatusSummary("not json"), "Unknown statuses");
});

test("formats export record statuses for history", () => {
  assert.equal(formatExportRecordStatus("running"), "Running");
  assert.equal(formatExportRecordStatus("complete"), "Complete");
  assert.equal(formatExportRecordStatus("failed"), "Failed");
});

test("explains export recovery for failed records", () => {
  assert.equal(
    exportRecoveryMessage("failed"),
    "Original photos remain unchanged. Adjust the selection or export folder and run export again.",
  );
  assert.equal(exportRecoveryMessage("running"), "");
  assert.equal(exportRecoveryMessage("complete"), "");
});

test("detects running export records", () => {
  assert.equal(hasRunningExport([{ status: "complete" }, { status: "failed" }]), false);
  assert.equal(hasRunningExport([{ status: "complete" }, { status: "running" }]), true);
});

test("allows downloads only for completed file exports", () => {
  assert.equal(isExportDownloadable({ mode: "csv", status: "complete" }), true);
  assert.equal(isExportDownloadable({ mode: "zip", status: "complete" }), true);
  assert.equal(isExportDownloadable({ mode: "folder", status: "complete" }), false);
  assert.equal(isExportDownloadable({ mode: "csv", status: "failed" }), false);
  assert.equal(isExportDownloadable({ mode: "zip", status: "running" }), false);
});
