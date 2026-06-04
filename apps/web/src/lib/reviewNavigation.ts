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
