import type { ProcessingJob } from "@/lib/api";

type ImportProcessBlockReason = {
  hasImportedPhotos: boolean;
  importStatus: ProcessingJob["status"] | null | undefined;
  isImportRunning: boolean;
};

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
