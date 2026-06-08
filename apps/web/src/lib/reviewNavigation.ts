export type ReviewPhotoRef = {
  id: string;
};

export type ReviewGroupRef = {
  id: string;
  representative_photo_id: string | null;
};

export type ReviewGroupedPhotoRef = ReviewPhotoRef & {
  group_id: string | null;
};

export type ReviewSelectionState<TPhoto extends ReviewGroupedPhotoRef, TGroup extends ReviewGroupRef> = {
  activeIndex: number;
  activePhoto: TPhoto | null;
  activeGroup: TGroup | null;
  compareCandidates: readonly TPhoto[];
};

type ReviewBatchScope = {
  activeGroupIndex: number;
  filter: string;
  loadedPhotoCount: number;
  photosPartiallyLoaded: boolean;
  projectPhotoCount: number;
  visiblePhotoCount: number;
};

type ReviewEmptyState = {
  hasActiveGroup: boolean;
  filter: string;
  loadedPhotoCount: number;
  photosPartiallyLoaded: boolean;
  projectPhotoCount: number;
};

type ReviewSaveFailure = {
  errorMessage: string;
  isBatch: boolean;
};

type ReviewAssetFallback = {
  assetType: "preview" | "thumbnail";
  hasAssetUrl: boolean;
};

type ReviewLoadRecoveryScope = "groups" | "photos" | "workspace";

function photoCountLabel(count: number): string {
  return `${count} ${count === 1 ? "photo" : "photos"}`;
}

function hasActiveReviewFilter(filter: string): boolean {
  return filter !== "All";
}

export function reviewBatchScopeSummary({
  activeGroupIndex,
  filter,
  visiblePhotoCount,
}: Pick<ReviewBatchScope, "activeGroupIndex" | "filter" | "visiblePhotoCount">): string {
  const countLabel = photoCountLabel(visiblePhotoCount);

  if (activeGroupIndex >= 0) {
    return `Group ${activeGroupIndex + 1} · ${countLabel}`;
  }

  if (hasActiveReviewFilter(filter)) {
    return `${filter} · ${countLabel}`;
  }

  return countLabel;
}

export function reviewBatchScopeDetail({
  activeGroupIndex,
  filter,
  loadedPhotoCount,
  photosPartiallyLoaded,
  projectPhotoCount,
  visiblePhotoCount,
}: ReviewBatchScope): string {
  if (!visiblePhotoCount) {
    if (activeGroupIndex >= 0) {
      return hasActiveReviewFilter(filter)
        ? `No loaded photos in this group match the ${filter} filter.`
        : "No loaded photos are available in this group.";
    }

    return hasActiveReviewFilter(filter)
      ? `No loaded photos match the ${filter} filter.`
      : "No loaded photos are available to batch mark.";
  }

  const scope =
    activeGroupIndex >= 0
      ? `Applies only to loaded photos in Group ${activeGroupIndex + 1}${
          hasActiveReviewFilter(filter) ? ` matching ${filter}` : ""
        }.`
      : hasActiveReviewFilter(filter)
        ? `Applies only to loaded photos matching ${filter}.`
        : `Applies to all ${photoCountLabel(loadedPhotoCount)} currently loaded.`;

  if (!photosPartiallyLoaded) {
    return scope;
  }

  return `${scope} Load all photos before batch marking if you need the full project of ${photoCountLabel(projectPhotoCount)}.`;
}

export function reviewEmptyStateMessage({
  hasActiveGroup,
  filter,
  loadedPhotoCount,
  photosPartiallyLoaded,
  projectPhotoCount,
}: ReviewEmptyState): { detail: string; title: string } {
  const loadedPrefix = photosPartiallyLoaded ? "loaded " : "";
  const filterSuffix = hasActiveReviewFilter(filter) ? ` match the ${filter} filter` : " are available";
  const scope = hasActiveGroup ? "in this group" : "";
  const title = hasActiveGroup
    ? `No ${loadedPrefix}photos ${scope}${filterSuffix}.`
    : `No ${loadedPrefix}photos${filterSuffix}.`;

  if (!photosPartiallyLoaded) {
    return { detail: "", title };
  }

  return {
    detail: `Only ${loadedPhotoCount} of ${photoCountLabel(projectPhotoCount)} are loaded.`,
    title,
  };
}

export function reviewSaveFailureMessage({ errorMessage, isBatch }: ReviewSaveFailure): string {
  const scope = isBatch ? "Batch update" : "Photo update";
  return `${scope} could not be saved. The visible status has been restored. ${errorMessage}`;
}

export function reviewAssetFallbackMessage({
  assetType,
  hasAssetUrl,
}: ReviewAssetFallback): { detail: string; shortTitle: string; title: string } {
  if (assetType === "thumbnail") {
    return hasAssetUrl
      ? {
          detail: "The generated local thumbnail could not load.",
          shortTitle: "Thumbnail failed",
          title: "Local thumbnail failed to load.",
        }
      : {
          detail: "No generated local thumbnail is available for this photo.",
          shortTitle: "No thumbnail",
          title: "No local thumbnail is available.",
        };
  }

  return hasAssetUrl
    ? {
        detail: "The original file remains unchanged. Reopen the project or rerun local processing to regenerate previews.",
        shortTitle: "Preview failed",
        title: "Local preview failed to load.",
      }
    : {
        detail: "Run import or processing again to create a local preview without modifying the original file.",
        shortTitle: "No preview",
        title: "No local preview is available.",
    };
}

export function reviewLoadRecoveryMessage(scope: ReviewLoadRecoveryScope): string {
  if (scope === "photos") {
    return "Confirm the local FramePilot API is running, then load all photos again. Review status changes already saved stay in the local project database.";
  }

  if (scope === "groups") {
    return "Confirm the local FramePilot API is running, then load all groups again. Existing grouping metadata stays in the local project database.";
  }

  return "Confirm the local FramePilot API is running, then reload the culling workspace. Original photos remain unchanged.";
}

export function nextPhotoIdAfterMark(
  visiblePhotos: readonly ReviewPhotoRef[],
  activePhotoId: string | null,
): string | null {
  if (!visiblePhotos.length) {
    return null;
  }

  const activeIndex = activePhotoId ? visiblePhotos.findIndex((photo) => photo.id === activePhotoId) : 0;
  const resolvedIndex = activeIndex >= 0 ? activeIndex : 0;
  const nextIndex = Math.min(resolvedIndex + 1, visiblePhotos.length - 1);

  if (nextIndex !== resolvedIndex) {
    return visiblePhotos[nextIndex].id;
  }

  return visiblePhotos[Math.max(resolvedIndex - 1, 0)].id;
}

export function groupAfterMove(
  groups: readonly ReviewGroupRef[],
  activeGroupId: string | null,
  delta: -1 | 1,
): ReviewGroupRef | null {
  if (!groups.length) {
    return null;
  }

  const activeIndex = activeGroupId ? groups.findIndex((group) => group.id === activeGroupId) : -1;
  if (activeIndex < 0) {
    return groups[0];
  }
  const resolvedIndex = activeIndex;
  const nextIndex = Math.min(Math.max(resolvedIndex + delta, 0), groups.length - 1);
  return groups[nextIndex];
}

export function reviewSelectionState<TPhoto extends ReviewGroupedPhotoRef, TGroup extends ReviewGroupRef>({
  activeGroupId,
  activePhotoId,
  filteredPhotos,
  groups,
  visiblePhotos,
}: {
  activeGroupId: string | null;
  activePhotoId: string | null;
  filteredPhotos: readonly TPhoto[];
  groups: readonly TGroup[];
  visiblePhotos: readonly TPhoto[];
}): ReviewSelectionState<TPhoto, TGroup> {
  const activeIndex = Math.max(
    0,
    visiblePhotos.findIndex((photo) => photo.id === activePhotoId),
  );
  const activePhoto = visiblePhotos[activeIndex] ?? visiblePhotos[0] ?? null;
  const groupId = activePhoto?.group_id ?? activeGroupId;
  const activeGroup = groupId ? (groups.find((group) => group.id === groupId) ?? null) : null;
  const compareCandidates = activeGroup
    ? filteredPhotos.filter((photo) => photo.group_id === activeGroup.id)
    : activePhoto
      ? [activePhoto]
      : [];

  return { activeGroup, activeIndex, activePhoto, compareCandidates };
}

export function windowedPhotoRefs<T extends ReviewPhotoRef>(
  photos: readonly T[],
  activePhotoId: string | null,
  maxItems: number,
): readonly T[] {
  if (maxItems <= 0 || photos.length <= maxItems) {
    return photos;
  }

  const activeIndex = activePhotoId ? photos.findIndex((photo) => photo.id === activePhotoId) : 0;
  const resolvedIndex = activeIndex >= 0 ? activeIndex : 0;
  const halfWindow = Math.floor(maxItems / 2);
  const start = Math.min(Math.max(resolvedIndex - halfWindow, 0), photos.length - maxItems);
  return photos.slice(start, start + maxItems);
}

export function windowedGroupRefs<T extends ReviewGroupRef>(
  groups: readonly T[],
  activeGroupId: string | null,
  maxItems: number,
): readonly T[] {
  if (maxItems <= 0 || groups.length <= maxItems) {
    return groups;
  }

  const activeIndex = activeGroupId ? groups.findIndex((group) => group.id === activeGroupId) : 0;
  const resolvedIndex = activeIndex >= 0 ? activeIndex : 0;
  const halfWindow = Math.floor(maxItems / 2);
  const start = Math.min(Math.max(resolvedIndex - halfWindow, 0), groups.length - maxItems);
  return groups.slice(start, start + maxItems);
}

export function windowedCompareRefs<T extends ReviewPhotoRef>(
  photos: readonly T[],
  activePhotoId: string | null,
  maxItems: number,
): readonly T[] {
  return windowedPhotoRefs(photos, activePhotoId, maxItems);
}
