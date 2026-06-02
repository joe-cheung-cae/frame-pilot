import type { Photo } from "@/lib/api";

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
