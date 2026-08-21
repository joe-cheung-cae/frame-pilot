import test from "node:test";
import assert from "node:assert/strict";

import { api } from "./api.ts";
import {
  importPathProgress,
  importPathProgressMessage,
  importPreviewCompletionMessage,
  importLoadRecoveryMessage,
  importProcessBlockMessage,
  importRegistrationMessage,
  importRegistrationTone,
  importSelectionBlockMessage,
  importTerminalStatusMessage,
  loadAvailableImportedPhotos,
  loadAvailableImportedPhotosForJob,
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

test("ignores an old import completion refresh after a newer import starts", async () => {
  let currentJobId: string | null = "job-1";
  let finishLoading: ((photo: { id: string }) => void) | undefined;
  const pending = loadAvailableImportedPhotosForJob(
    "job-1",
    ["photo-1"],
    () =>
      new Promise<{ id: string }>((resolve) => {
        finishLoading = resolve;
      }),
    () => currentJobId,
  );

  currentJobId = "job-2";
  finishLoading?.({ id: "photo-1" });

  assert.equal(await pending, null);
});

test("explains why import must finish before processing", () => {
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: true, importStatus: "running", isImportRunning: true }),
    "Wait for import previews to finish before processing this project.",
  );
});

test("allows processing existing photos after failed and cancelled imports", () => {
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: true, importStatus: "failed", isImportRunning: false }),
    "",
  );
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: true, importStatus: "cancelled", isImportRunning: false }),
    "",
  );
});

test("explains failed and cancelled import blockers when no photos are available", () => {
  assert.equal(
    importProcessBlockMessage({ hasImportedPhotos: false, importStatus: "failed", isImportRunning: false }),
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

function remainingFilePaths(start: number, count: number): string[] {
  return Array.from(
    { length: count },
    (_, index) => `/abs/burst/frame-${String(start + index).padStart(3, "0")}.jpg`,
  );
}

function pathImportJob(id: string, totalItems: number) {
  return {
    id,
    project_id: "project-1",
    job_type: "import",
    status: "running",
    current_step: "receive_files",
    total_items: totalItems,
    processed_items: 0,
    failed_items: 0,
    progress_percent: 0,
    error_message: null,
    cancellation_requested: false,
    cancelled_at: null,
    started_at: null,
    completed_at: null,
    retryable: false,
  };
}

function pathImportSliceResult(options: {
  importedCount: number;
  startIndex: number;
  remainingPaths: string[];
  expandedTotal: number;
  jobId?: string;
}) {
  return {
    imported: Array.from({ length: options.importedCount }, (_, index) => ({
      id: `photo-${options.startIndex + index}`,
      filename: `frame-${String(options.startIndex + index).padStart(3, "0")}.jpg`,
    })),
    skipped: [],
    job: pathImportJob(options.jobId ?? "job-1", options.expandedTotal),
    total_files: options.importedCount,
    accepted_files: options.importedCount,
    skipped_files: 0,
    failed_files: 0,
    remaining_paths: options.remainingPaths,
    expanded_total: options.expandedTotal,
    timing: null,
  };
}

async function withMockedFetch<T>(
  handler: (url: string, init?: RequestInit) => Promise<Response> | Response,
  run: () => Promise<T>,
): Promise<T> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    return handler(url, init);
  }) as typeof fetch;
  try {
    return await run();
  } finally {
    globalThis.fetch = originalFetch;
  }
}

test("path import progress uses expanded_total rather than the current slice size", () => {
  const remaining150 = remainingFilePaths(100, 150);
  assert.deepEqual(importPathProgress({ expanded_total: 250, remaining_paths: remaining150 }), {
    completed: 100,
    remaining: 150,
    total: 250,
  });
  assert.equal(
    importPathProgressMessage({ expanded_total: 250, remaining_paths: remaining150 }),
    "Registered 100 of 250 files from local paths.",
  );
  assert.equal(
    importPathProgressMessage({ expanded_total: 1, remaining_paths: [] }),
    "Registered 1 of 1 file from local paths.",
  );
  assert.equal(importPathProgressMessage({ expanded_total: null, remaining_paths: [] }), "Registering files from local paths...");
});

test("importPhotosFromPaths loops remaining_paths with the same job_id and finalizes the last slice only", async () => {
  const folder = "/abs/burst";
  const remaining150 = remainingFilePaths(100, 150);
  const remaining50 = remainingFilePaths(200, 50);
  const calls: { url: string; body: Record<string, unknown> }[] = [];
  const progressTotals: number[] = [];

  const result = await withMockedFetch(
    async (url, init) => {
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      calls.push({ url, body });
      if (calls.length === 1) {
        return new Response(
          JSON.stringify(
            pathImportSliceResult({
              importedCount: 100,
              startIndex: 0,
              remainingPaths: remaining150,
              expandedTotal: 250,
            }),
          ),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      if (calls.length === 2) {
        return new Response(
          JSON.stringify(
            pathImportSliceResult({
              importedCount: 100,
              startIndex: 100,
              remainingPaths: remaining50,
              expandedTotal: 250,
            }),
          ),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(
        JSON.stringify(
          pathImportSliceResult({
            importedCount: 50,
            startIndex: 200,
            remainingPaths: [],
            expandedTotal: 250,
          }),
        ),
        { status: 201, headers: { "Content-Type": "application/json" } },
      );
    },
    () =>
      api.importPhotosFromPaths("project-1", [folder], {
        onSliceComplete: (_slice, _index, expandedTotal) => {
          progressTotals.push(expandedTotal);
        },
      }),
  );

  assert.equal(calls.length, 3);
  assert.equal(calls.every((call) => call.url.endsWith("/api/projects/project-1/imports/from-paths")), true);
  assert.deepEqual(calls[0]?.body, {
    paths: [folder],
    job_id: null,
    expected_total: null,
    finalize: false,
  });
  assert.deepEqual(calls[1]?.body, {
    paths: remaining150,
    job_id: "job-1",
    expected_total: 250,
    finalize: false,
  });
  assert.deepEqual(calls[2]?.body, {
    paths: remaining50,
    job_id: "job-1",
    expected_total: 250,
    finalize: true,
  });
  assert.equal(result.imported.length, 250);
  assert.equal(result.expanded_total, 250);
  assert.deepEqual(result.remaining_paths, []);
  assert.equal(result.job?.id, "job-1");
  assert.deepEqual(progressTotals, [250, 250, 250]);
});

test("importPhotosFromPaths finalizes a small folder after remaining_paths is empty", async () => {
  const folder = "/abs/card";
  const calls: Record<string, unknown>[] = [];

  await withMockedFetch(
    async (_url, init) => {
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      calls.push(body);
      return new Response(
        JSON.stringify(
          pathImportSliceResult({
            importedCount: 2,
            startIndex: 0,
            remainingPaths: [],
            expandedTotal: 2,
          }),
        ),
        { status: 201, headers: { "Content-Type": "application/json" } },
      );
    },
    () => api.importPhotosFromPaths("project-1", [folder]),
  );

  assert.equal(calls.length, 2);
  assert.equal(calls[0]?.finalize, false);
  assert.equal(calls[0]?.job_id, null);
  assert.deepEqual(calls[0]?.paths, [folder]);
  assert.equal(calls[1]?.finalize, true);
  assert.equal(calls[1]?.job_id, "job-1");
  assert.equal(calls[1]?.expected_total, 2);
  assert.deepEqual(calls[1]?.paths, []);
});

test("importPhotosFromPaths finalizes a small image-file selection on the first slice", async () => {
  const files = ["/abs/a.jpg", "/abs/b.png"];
  const calls: Record<string, unknown>[] = [];

  await withMockedFetch(
    async (_url, init) => {
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      calls.push(body);
      return new Response(
        JSON.stringify(
          pathImportSliceResult({
            importedCount: 2,
            startIndex: 0,
            remainingPaths: [],
            expandedTotal: 2,
          }),
        ),
        { status: 201, headers: { "Content-Type": "application/json" } },
      );
    },
    () => api.importPhotosFromPaths("project-1", files),
  );

  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0], {
    paths: files,
    job_id: null,
    expected_total: null,
    finalize: true,
  });
});

test("importPhotosFromPaths rejects an empty path list", async () => {
  await assert.rejects(() => api.importPhotosFromPaths("project-1", []), /At least one path is required/);
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
