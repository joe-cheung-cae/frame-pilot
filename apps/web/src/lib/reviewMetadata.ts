export type ReviewMetadataPhoto = {
  aperture: string | null;
  camera_model: string | null;
  capture_time: string | null;
  focal_length: string | null;
  iso: number | null;
  lens_model: string | null;
  shutter_speed: string | null;
};

export type ReviewMetadataRow = [label: string, value: string];

export function formatCaptureTime(value: string | null): string | null {
  return value ? value.replace("T", " ").slice(0, 16) : null;
}

export function reviewMetadataRows(photo: ReviewMetadataPhoto | null): ReviewMetadataRow[] {
  if (!photo) {
    return [];
  }

  return [
    ["Captured", formatCaptureTime(photo.capture_time)],
    ["Camera", photo.camera_model],
    ["Lens", photo.lens_model],
    ["Focal length", photo.focal_length ? `${photo.focal_length} mm` : null],
    ["Aperture", photo.aperture ? `f/${photo.aperture}` : null],
    ["Shutter", photo.shutter_speed],
    ["ISO", photo.iso ? String(photo.iso) : null],
  ].filter((row): row is ReviewMetadataRow => Boolean(row[1]));
}
