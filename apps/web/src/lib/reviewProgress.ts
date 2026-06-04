export type ReviewProgress = {
  activeGroupId: string | null;
  activePhotoId: string | null;
  compareMode: boolean;
  filter: string;
  largePreview: boolean;
  zoomPreview: boolean;
};

export const DEFAULT_REVIEW_PROGRESS: ReviewProgress = {
  activeGroupId: null,
  activePhotoId: null,
  compareMode: false,
  filter: "All",
  largePreview: false,
  zoomPreview: false,
};

const STORAGE_PREFIX = "framepilot.reviewProgress.v1";

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

export function reviewProgressStorageKey(projectId: string): string {
  return `${STORAGE_PREFIX}.${projectId}`;
}

export function normalizeReviewProgress(value: unknown, allowedFilters: readonly string[]): ReviewProgress {
  if (!value || typeof value !== "object") {
    return DEFAULT_REVIEW_PROGRESS;
  }

  const candidate = value as Record<string, unknown>;
  const filter = typeof candidate.filter === "string" && allowedFilters.includes(candidate.filter) ? candidate.filter : "All";

  return {
    activeGroupId: stringOrNull(candidate.activeGroupId),
    activePhotoId: stringOrNull(candidate.activePhotoId),
    compareMode: typeof candidate.compareMode === "boolean" ? candidate.compareMode : false,
    filter,
    largePreview: typeof candidate.largePreview === "boolean" ? candidate.largePreview : false,
    zoomPreview: typeof candidate.zoomPreview === "boolean" ? candidate.zoomPreview : false,
  };
}

export function parseReviewProgress(rawValue: string | null, allowedFilters: readonly string[]): ReviewProgress {
  if (!rawValue) {
    return DEFAULT_REVIEW_PROGRESS;
  }

  try {
    return normalizeReviewProgress(JSON.parse(rawValue), allowedFilters);
  } catch {
    return DEFAULT_REVIEW_PROGRESS;
  }
}

export function reviewProgressForEntry(
  rawValue: string | null,
  allowedFilters: readonly string[],
  requestedFilter: string | null | undefined,
): ReviewProgress {
  const storedProgress = parseReviewProgress(rawValue, allowedFilters);
  const validRequestedFilter =
    typeof requestedFilter === "string" && allowedFilters.includes(requestedFilter) ? requestedFilter : null;

  return {
    ...storedProgress,
    activeGroupId: validRequestedFilter ? null : storedProgress.activeGroupId,
    activePhotoId: validRequestedFilter ? null : storedProgress.activePhotoId,
    filter: validRequestedFilter ?? storedProgress.filter,
  };
}
