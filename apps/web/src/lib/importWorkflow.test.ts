import test from "node:test";
import assert from "node:assert/strict";

import {
  importPreviewCompletionMessage,
  importLoadRecoveryMessage,
  importProcessBlockMessage,
  importRegistrationMessage,
  importRegistrationTone,
  importSelectionBlockMessage,
  importTerminalStatusMessage,
  loadAvailableImportedPhotos,
} from "./importWorkflow.ts";

test("summarizes import registration before preview generation", () => {
  assert.equal(
    importRegistrationMessage({ importedCount: 2, skippedCount: 0 }),
    "2 images registered. Generating previews...",
  );
  assert.equal(
    importRegistrationMessage({ importedCount: 1, skippedCount: 2 }),
    "1 image registered. Generating previews... 2 files skipped.",
  );
});

test("explains import registration with no supported images", () => {
  assert.equal(
    importRegistrationMessage({ importedCount: 0, skippedCount: 3 }),
    "3 files skipped. No supported images were registered.",
  );
  assert.equal(importRegistrationMessage({ importedCount: 0, skippedCount: 0 }), "No images were registered.");
});

test("classifies import registration feedback tone", () => {
  assert.equal(importRegistrationTone({ importedCount: 2, skippedCount: 0 }), "success");
  assert.equal(importRegistrationTone({ importedCount: 1, skippedCount: 2 }), "neutral");
  assert.equal(importRegistrationTone({ importedCount: 0, skippedCount: 3 }), "warning");
  assert.equal(importRegistrationTone({ importedCount: 0, skippedCount: 0 }), "warning");
});

test("summarizes preview completion only when images were imported", () => {
  assert.equal(importPreviewCompletionMessage(2), "2 images imported and previewed.");
  assert.equal(importPreviewCompletionMessage(1), "1 image imported and previewed.");
  assert.equal(importPreviewCompletionMessage(0), "");
});

test("keeps available recent imports when one photo refresh fails", async () => {
  const photos = await loadAvailableImportedPhotos(["photo-1", "photo-2", "photo-3"], async (photoId) => {
    if (photoId === "photo-2") {
      throw new Error("Photo unavailable");
    }
    return { id: photoId };
  });

  assert.deepEqual(photos, [{ id: "photo-1" }, { id: "photo-3" }]);
});

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
    importSelectionBlockMessage({ isCancelling: true, isImportRunning: true, isRetrying: false }),
    "Cancellation is being requested. Wait for FramePilot to reach a safe checkpoint.",
  );
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

test("explains failed import terminal states", () => {
  assert.equal(
    importTerminalStatusMessage({ retryable: true, status: "failed" }),
    "Import failed. Retry will regenerate missing local previews without modifying original files.",
  );
  assert.equal(
    importTerminalStatusMessage({ retryable: false, status: "failed" }),
    "Import failed. Add the images again to restart local preview generation without modifying original files.",
  );
});

test("explains cancelled import terminal states", () => {
  assert.equal(
    importTerminalStatusMessage({ retryable: true, status: "cancelled" }),
    "Import was cancelled at a safe checkpoint. Retry will regenerate missing local previews without modifying original files.",
  );
  assert.equal(
    importTerminalStatusMessage({ retryable: false, status: "cancelled" }),
    "Import was cancelled at a safe checkpoint. Add more images when you are ready.",
  );
});

test("omits terminal import guidance for non-terminal statuses", () => {
  assert.equal(importTerminalStatusMessage({ retryable: true, status: "running" }), "");
  assert.equal(importTerminalStatusMessage({ retryable: false, status: "complete" }), "");
  assert.equal(importTerminalStatusMessage({ retryable: false, status: null }), "");
});

test("explains how to recover from import data load and action failures", () => {
  assert.equal(
    importLoadRecoveryMessage("project"),
    "Confirm the local FramePilot API is running, then reload the import page. Project data stays on this computer.",
  );
  assert.equal(
    importLoadRecoveryMessage("import"),
    "Confirm the local FramePilot API is running, then choose the files again. Original source photos remain unchanged.",
  );
  assert.equal(
    importLoadRecoveryMessage("retry"),
    "Confirm the local FramePilot API is running, then retry local preview generation. Original source photos remain unchanged.",
  );
  assert.equal(
    importLoadRecoveryMessage("cancel"),
    "Confirm the local FramePilot API is running. If cancellation did not reach the job, FramePilot will keep the original files unchanged.",
  );
  assert.equal(
    importLoadRecoveryMessage("job"),
    "Confirm the local FramePilot API is running, then reload import status. Local job records stay in the project database.",
  );
});
