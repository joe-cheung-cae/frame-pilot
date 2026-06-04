export type ReviewScorePhoto = {
  aesthetic_score: number;
  blur_score: number;
  contrast_score: number;
  exposure_score: number;
  eye_open_confidence: number | null;
  face_quality_score: number;
  face_sharpness_score: number;
  overall_score: number;
  sharpness_score: number;
};

export type ReviewScoreRow = [label: string, value: string];

function formatScore(value: number | null): string {
  return Number(value ?? 0).toFixed(2);
}

export function reviewScoreRows(photo: ReviewScorePhoto): ReviewScoreRow[] {
  return [
    ["Sharpness", formatScore(photo.sharpness_score)],
    ["Exposure", formatScore(photo.exposure_score)],
    ["Contrast", formatScore(photo.contrast_score)],
    ["Blur risk", formatScore(photo.blur_score)],
    ["Face sharpness", formatScore(photo.face_sharpness_score)],
    ["Eye open", formatScore(photo.eye_open_confidence)],
    ["Face quality", formatScore(photo.face_quality_score)],
    ["Aesthetic", formatScore(photo.aesthetic_score)],
    ["Overall", formatScore(photo.overall_score)],
  ];
}
