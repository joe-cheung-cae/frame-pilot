export type ReviewPhotoRef = {
  id: string;
};

export function nextPhotoIdAfterMark(visiblePhotos: readonly ReviewPhotoRef[], activePhotoId: string | null): string | null {
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
