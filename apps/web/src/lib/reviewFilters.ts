import type { Photo } from "./api.ts";

export const PROCESSING_FAILURE_FILTER = "Processing failures";

export const REVIEW_FILTERS = [
  "All",
  "Picks",
  "Maybes",
  "Rejects",
  "Unreviewed",
  "AI recommended",
  "Blurry photos",
  PROCESSING_FAILURE_FILTER,
  "Duplicate groups",
  "Photos with faces",
] as const;

export type ReviewFilter = (typeof REVIEW_FILTERS)[number];

export function isReviewFilter(value: string | null | undefined): value is ReviewFilter {
  return Boolean(value && (REVIEW_FILTERS as readonly string[]).includes(value));
}

export type ReviewFilterPhoto = Pick<
  Photo,
  | "ai_recommendation"
  | "blur_score"
  | "face_presence"
  | "group_id"
  | "processing_error"
  | "processing_state"
  | "user_status"
>;

export function photoMatchesReviewFilter(
  photo: ReviewFilterPhoto,
  filter: string,
  duplicateGroupIds: ReadonlySet<string>,
): boolean {
  if (filter === "All") return true;
  if (filter === "Picks") return photo.user_status === "Pick";
  if (filter === "Maybes") return photo.user_status === "Maybe";
  if (filter === "Rejects") return photo.user_status === "Reject";
  if (filter === "Unreviewed") return photo.user_status === "Unreviewed";
  if (filter === "AI recommended") return photo.ai_recommendation === "Pick";
  if (filter === "Blurry photos") return photo.blur_score >= 0.55;
  if (filter === PROCESSING_FAILURE_FILTER) return photo.processing_state === "failed" || Boolean(photo.processing_error);
  if (filter === "Duplicate groups") return Boolean(photo.group_id && duplicateGroupIds.has(photo.group_id));
  if (filter === "Photos with faces") return photo.face_presence;
  return true;
}
