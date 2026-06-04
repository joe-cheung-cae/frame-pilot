export type ReviewHeaderPhoto = {
  user_status: "Pick" | "Maybe" | "Reject" | "Unreviewed";
};

export function reviewHeaderSummary({
  activeGroupIndex,
  groupCount,
  photos,
  photosPartiallyLoaded,
  projectPhotoCount,
}: {
  activeGroupIndex: number;
  groupCount: number;
  photos: readonly ReviewHeaderPhoto[];
  photosPartiallyLoaded: boolean;
  projectPhotoCount: number;
}): string {
  const picks = photos.filter((photo) => photo.user_status === "Pick").length;
  const reviewed = photos.filter((photo) => photo.user_status !== "Unreviewed").length;
  return `${reviewed}/${photos.length} loaded reviewed · ${picks} loaded picks${
    photosPartiallyLoaded ? ` · ${photos.length} of ${projectPhotoCount} loaded` : ""
  }${activeGroupIndex >= 0 ? ` · Group ${activeGroupIndex + 1} of ${groupCount}` : ""}`;
}
