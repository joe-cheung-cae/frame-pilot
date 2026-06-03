export type ReviewPhotoRef = {
  id: string;
};

export type ReviewGroupRef = {
  id: string;
  representative_photo_id: string | null;
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
