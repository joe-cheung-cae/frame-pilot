import type { ExportRecord, Photo } from "@/lib/api";

export type ExportStatus = Photo["user_status"];

export const EXPORT_STATUSES: ExportStatus[] = ["Pick", "Maybe", "Reject", "Unreviewed"];

export function countPhotosByStatus(photos: readonly Pick<Photo, "user_status">[]): Record<ExportStatus, number> {
  const counts: Record<ExportStatus, number> = { Pick: 0, Maybe: 0, Reject: 0, Unreviewed: 0 };
  for (const photo of photos) {
    counts[photo.user_status] += 1;
  }
  return counts;
}

export function selectedPhotoCount(counts: Record<ExportStatus, number>, statuses: readonly ExportStatus[]): number {
  return statuses.reduce((total, status) => total + counts[status], 0);
}

export function exportActionBlockMessage({
  isExporting,
  isStatusCountsLoading,
  selectedCount,
  selectedStatuses,
}: {
  isExporting: boolean;
  isStatusCountsLoading: boolean;
  selectedCount: number;
  selectedStatuses: readonly ExportStatus[];
}): string {
  if (isExporting) {
    return "Export is running. Wait for it to finish before changing export settings.";
  }

  if (isStatusCountsLoading) {
    return "Loading photo status counts before export.";
  }

  if (!selectedStatuses.length) {
    return "Choose at least one status to export.";
  }

  if (selectedCount === 0) {
    return "No photos match the selected statuses.";
  }

  return "";
}

export function applyStatusCountChange(
  counts: Record<ExportStatus, number>,
  previousStatus: ExportStatus,
  nextStatus: ExportStatus,
): Record<ExportStatus, number> {
  if (previousStatus === nextStatus) {
    return { ...counts };
  }
  return {
    ...counts,
    [previousStatus]: Math.max(0, counts[previousStatus] - 1),
    [nextStatus]: counts[nextStatus] + 1,
  };
}

export function formatExportStatusSummary(rawStatuses: string): string {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawStatuses);
  } catch {
    return "Unknown statuses";
  }

  if (!Array.isArray(parsed)) {
    return "Unknown statuses";
  }

  const selected = EXPORT_STATUSES.filter((status) => parsed.includes(status));
  return selected.length ? selected.join(", ") : "No statuses";
}

export function isExportDownloadable(record: Pick<ExportRecord, "mode" | "status">): boolean {
  return record.status === "complete" && record.mode !== "folder";
}
