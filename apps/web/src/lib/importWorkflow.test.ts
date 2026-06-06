import test from "node:test";
import assert from "node:assert/strict";

import { importProcessBlockMessage, importSelectionBlockMessage } from "./importWorkflow.ts";

test("explains why import must finish before processing", () => {
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: true, importStatus: "running", isImportRunning: true }),
    "Wait for import previews to finish before processing this project.",
  );
});

test("explains failed and cancelled import blockers", () => {
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: true, importStatus: "failed", isImportRunning: false }),
    "Retry the failed import before processing this project.",
  );
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: false, importStatus: "cancelled", isImportRunning: false }),
    "Retry import or add more images before processing this project.",
  );
});

test("explains missing imported photos before processing", () => {
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: false, importStatus: null, isImportRunning: false }),
    "Import images before processing this project.",
  );
});

test("returns no process blocker when imports are ready", () => {
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: true, importStatus: "complete", isImportRunning: false }),
    "",
  );
});

test("explains why import selection is blocked during active import work", () => {
  assert.equal(
    importSelectionBlockMessage({ isCancelling: false, isImportRunning: true, isRetrying: false }),
    "Import is running. Wait for the current import to finish before adding more files.",
  );
  assert.equal(
    importSelectionBlockMessage({ isCancelling: false, isImportRunning: false, isRetrying: true }),
    "Import retry is starting. Wait for the retry job to appear before choosing more files.",
  );
  assert.equal(
    importSelectionBlockMessage({ isCancelling: true, isImportRunning: false, isRetrying: false }),
    "Cancellation is being requested. Wait for FramePilot to reach a safe checkpoint.",
  );
});

test("allows import selection when no import work is active", () => {
  assert.equal(
    importSelectionBlockMessage({ isCancelling: false, isImportRunning: false, isRetrying: false }),
    "",
  );
});
