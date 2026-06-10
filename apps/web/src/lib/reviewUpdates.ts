import type { Photo, PhotoPatch } from "./api";

const REVIEW_UPDATE_FIELDS = ["user_status", "star_rating"] as const;

function photoStillMatchesPatch(photo: Photo, patch: PhotoPatch) {
  return REVIEW_UPDATE_FIELDS.every((field) => patch[field] === undefined || photo[field] === patch[field]);
}

function mergePatchedFields(photo: Photo, source: Photo, patch: PhotoPatch) {
  return {
    ...photo,
    ...(patch.user_status !== undefined ? { user_status: source.user_status } : {}),
    ...(patch.star_rating !== undefined ? { star_rating: source.star_rating } : {}),
  };
}

export function rollbackOptimisticPhotoUpdates(
  currentPhotos: readonly Photo[],
  previousPhotos: readonly Photo[],
  patch: PhotoPatch,
) {
  const previousById = new Map(previousPhotos.map((photo) => [photo.id, photo]));
  const rolledBackPhotos: Photo[] = [];
  const photos = currentPhotos.map((photo) => {
    const previousPhoto = previousById.get(photo.id);
    if (!previousPhoto || !photoStillMatchesPatch(photo, patch)) {
      return photo;
    }

    rolledBackPhotos.push(previousPhoto);
    return mergePatchedFields(photo, previousPhoto, patch);
  });

  return { photos, rolledBackPhotos };
}

export function reconcileOptimisticPhotoUpdates(
  currentPhotos: readonly Photo[],
  updatedPhotos: readonly Photo[],
  patch: PhotoPatch,
) {
  const updatedById = new Map(updatedPhotos.map((photo) => [photo.id, photo]));

  return currentPhotos.map((photo) => {
    const updatedPhoto = updatedById.get(photo.id);
    if (!updatedPhoto || !photoStillMatchesPatch(photo, patch)) {
      return photo;
    }

    return mergePatchedFields(photo, updatedPhoto, patch);
  });
}

export function mergeLoadedPhotosWithCurrentReviews(
  loadedPhotos: readonly Photo[],
  currentPhotos: readonly Photo[],
) {
  const currentById = new Map(currentPhotos.map((photo) => [photo.id, photo]));

  return loadedPhotos.map((loadedPhoto) => {
    const currentPhoto = currentById.get(loadedPhoto.id);
    if (!currentPhoto) return loadedPhoto;

    return {
      ...loadedPhoto,
      user_status: currentPhoto.user_status,
      star_rating: currentPhoto.star_rating,
    };
  });
}
