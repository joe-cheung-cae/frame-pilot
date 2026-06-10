import test from "node:test";
import assert from "node:assert/strict";

import type { Photo, PhotoPatch } from "./api.ts";
import {
  reconcileOptimisticPhotoUpdates,
  rollbackOptimisticPhotoUpdates,
} from "./reviewUpdates.ts";

function photo(id: string, userStatus: Photo["user_status"], starRating = 0): Photo {
  return {
    id,
    project_id: "project-1",
    filename: `${id}.jpg`,
    file_ext: ".jpg",
    file_size: 1,
    file_mtime: null,
    content_hash: null,
    project_copy_path: `/photos/${id}.jpg`,
    source_identity: null,
    width: 1,
    height: 1,
    capture_time: null,
    camera_model: null,
    lens_model: null,
    focal_length: null,
    aperture: null,
    shutter_speed: null,
    iso: null,
    thumbnail_path: null,
    preview_path: null,
    perceptual_hash: null,
    sharpness_score: 0,
    blur_score: 0,
    exposure_score: 0,
    contrast_score: 0,
    noise_score: 0,
    face_presence: false,
    face_sharpness_score: 0,
    eye_open_confidence: null,
    face_quality_score: 0,
    aesthetic_score: 0,
    overall_score: 0,
    ai_recommendation: "",
    recommendation_explanation: "",
    user_status: userStatus,
    star_rating: starRating,
    group_id: null,
    processing_state: "processed",
    processing_error: null,
  };
}

test("rolls back only failed targets while preserving newer photo updates", () => {
  const previousPhotos = [photo("first", "Unreviewed")];
  const currentPhotos = [photo("first", "Pick"), photo("second", "Pick")];
  const patch: PhotoPatch = { user_status: "Pick" };

  const result = rollbackOptimisticPhotoUpdates(currentPhotos, previousPhotos, patch);

  assert.deepEqual(
    result.photos.map(({ id, user_status }) => ({ id, user_status })),
    [
      { id: "first", user_status: "Unreviewed" },
      { id: "second", user_status: "Pick" },
    ],
  );
  assert.deepEqual(result.rolledBackPhotos.map(({ id }) => ({ id })), [{ id: "first" }]);
});

test("does not roll back a target after a newer same-field update", () => {
  const result = rollbackOptimisticPhotoUpdates(
    [photo("first", "Reject")],
    [photo("first", "Unreviewed")],
    { user_status: "Pick" },
  );

  assert.equal(result.photos[0].user_status, "Reject");
  assert.deepEqual(result.rolledBackPhotos, []);
});

test("merges successful fields without overwriting a newer unrelated update", () => {
  const result = reconcileOptimisticPhotoUpdates(
    [photo("first", "Pick", 4)],
    [photo("first", "Pick", 0)],
    { user_status: "Pick" },
  );

  assert.equal(result[0].user_status, "Pick");
  assert.equal(result[0].star_rating, 4);
});

test("ignores a stale successful response after a newer same-field update", () => {
  const result = reconcileOptimisticPhotoUpdates(
    [photo("first", "Reject")],
    [photo("first", "Pick")],
    { user_status: "Pick" },
  );

  assert.equal(result[0].user_status, "Reject");
});
