import type { ProcessingJob } from "@/lib/api";

type ImportRegistrationSummary = {
  importedCount: number;
  skippedCount: number;
};
export type ImportFeedbackTone = "neutral" | "success" | "warning";

type ImportProcessBlockReason = {
  hasImportedPhotos: boolean;
  importStatus: ProcessingJob["status"] | null | undefined;
  isImportRunning: boolean;
};

type ImportSelectionBlockReason = {
  isCancelling: boolean;
  isImportRunning: boolean;
  isRetrying: boolean;
};

type ImportTerminalStatusReason = {
  retryable: boolean;
  status: ProcessingJob["status"] | null | undefined;
};

type ImportLoadScope = "cancel" | "import" | "job" | "project" | "retry";

function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return count === 1 ? singular : plural;
}

export function importRegistrationMessage({
  importedCount,
  skippedCount,
}: ImportRegistrationSummary): string {
  if (importedCount <= 0) {
    return skippedCount > 0
      ? `${skippedCount} ${pluralize(skippedCount, "file")} skipped. No supported images were registered.`
      : "No images were registered.";
  }

  const registered = `${importedCount} ${pluralize(importedCount, "image")} registered. Generating previews...`;
  if (skippedCount <= 0) {
    return registered;
  }

  return `${registered} ${skippedCount} ${pluralize(skippedCount, "file")} skipped.`;
}

export function importRegistrationTone({
  importedCount,
  skippedCount,
}: ImportRegistrationSummary): ImportFeedbackTone {
  if (importedCount <= 0) {
    return "warning";
  }

  return skippedCount > 0 ? "neutral" : "success";
}

export function importPreviewCompletionMessage(importedCount: number): string {
  if (importedCount <= 0) {
    return "";
  }

  return `${importedCount} ${pluralize(importedCount, "image")} imported and previewed.`;
}

export function importProcessBlockMessage({
  hasImportedPhotos,
  importStatus,
  isImportRunning,
}: ImportProcessBlockReason): string {
  if (isImportRunning) {
    return "Wait for import previews to finish before processing this project.";
  }

  if (importStatus === "failed") {
    return "Retry the failed import before processing this project.";
  }

  if (importStatus === "cancelled") {
    return "Retry import or add more images before processing this project.";
  }

  if (!hasImportedPhotos) {
    return "Import images before processing this project.";
  }

  return "";
}

export function importSelectionBlockMessage({
  isCancelling,
  isImportRunning,
  isRetrying,
}: ImportSelectionBlockReason): string {
  if (isCancelling) {
    return "Cancellation is being requested. Wait for FramePilot to reach a safe checkpoint.";
  }

  if (isImportRunning) {
    return "Import is running. Wait for the current import to finish before adding more files.";
  }

  if (isRetrying) {
    return "Import retry is starting. Wait for the retry job to appear before choosing more files.";
  }

  return "";
}

export function importTerminalStatusMessage({ retryable, status }: ImportTerminalStatusReason): string {
  if (status === "failed") {
    return retryable
      ? "Import failed. Retry will regenerate missing local previews without modifying original files."
      : "Import failed. Add the images again to restart local preview generation without modifying original files.";
  }

  if (status === "cancelled") {
    return retryable
      ? "Import was cancelled at a safe checkpoint. Retry will regenerate missing local previews without modifying original files."
      : "Import was cancelled at a safe checkpoint. Add more images when you are ready.";
  }

  return "";
}

export function importLoadRecoveryMessage(scope: ImportLoadScope): string {
  if (scope === "import") {
    return "Confirm the local FramePilot API is running, then choose the files again. Original source photos remain unchanged.";
  }

  if (scope === "retry") {
    return "Confirm the local FramePilot API is running, then retry local preview generation. Original source photos remain unchanged.";
  }

  if (scope === "cancel") {
    return "Confirm the local FramePilot API is running. If cancellation did not reach the job, FramePilot will keep the original files unchanged.";
  }

  if (scope === "job") {
    return "Confirm the local FramePilot API is running, then reload import status. Local job records stay in the project database.";
  }

  return "Confirm the local FramePilot API is running, then reload the import page. Project data stays on this computer.";
}
