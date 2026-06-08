import type { ProcessingJob } from "@/lib/api";

type ImportRegistrationSummary = {
  importedCount: number;
  skippedCount: number;
};

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
  if (isImportRunning) {
    return "Import is running. Wait for the current import to finish before adding more files.";
  }

  if (isRetrying) {
    return "Import retry is starting. Wait for the retry job to appear before choosing more files.";
  }

  if (isCancelling) {
    return "Cancellation is being requested. Wait for FramePilot to reach a safe checkpoint.";
  }

  return "";
}
