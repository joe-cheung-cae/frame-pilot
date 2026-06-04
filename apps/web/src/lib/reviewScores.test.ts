import test from "node:test";
import assert from "node:assert/strict";

import { reviewScoreRows } from "./reviewScores.ts";

test("builds formatted review score rows in panel order", () => {
  assert.deepEqual(
    reviewScoreRows({
      aesthetic_score: 0.83,
      blur_score: 0.123,
      contrast_score: 0.678,
      exposure_score: 0.5,
      eye_open_confidence: 0.918,
      face_quality_score: 0.456,
      face_sharpness_score: 0.234,
      overall_score: 0.999,
      sharpness_score: 0.875,
    }),
    [
      ["Sharpness", "0.88"],
      ["Exposure", "0.50"],
      ["Contrast", "0.68"],
      ["Blur risk", "0.12"],
      ["Face sharpness", "0.23"],
      ["Eye open", "0.92"],
      ["Face quality", "0.46"],
      ["Aesthetic", "0.83"],
      ["Overall", "1.00"],
    ],
  );
});

test("formats missing eye-open confidence as zero", () => {
  const rows = reviewScoreRows({
    aesthetic_score: 0,
    blur_score: 0,
    contrast_score: 0,
    exposure_score: 0,
    eye_open_confidence: null,
    face_quality_score: 0,
    face_sharpness_score: 0,
    overall_score: 0,
    sharpness_score: 0,
  });

  assert.deepEqual(rows.find(([label]) => label === "Eye open"), ["Eye open", "0.00"]);
});
