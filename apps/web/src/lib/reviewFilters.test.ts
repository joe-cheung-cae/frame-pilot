import test from "node:test";
import assert from "node:assert/strict";

import {
  isReviewFilter,
  photoMatchesReviewFilter,
  PROCESSING_FAILURE_FILTER,
  REVIEW_FILTERS,
  type ReviewFilterPhoto,
} from "./reviewFilters.ts";

function photo(overrides: Partial<ReviewFilterPhoto> = {}): ReviewFilterPhoto {
  return {
    ai_recommendation: "Maybe",
    blur_score: 0.1,
    face_presence: false,
    group_id: null,
    processing_error: null,
    processing_state: "processed",
    user_status: "Unreviewed",
    ...overrides,
  };
}

test("keeps review filter order stable", () => {
  assert.deepEqual(REVIEW_FILTERS, [
    "All",
    "Picks",
    "Maybes",
    "Rejects",
    "Unreviewed",
    "AI recommended",
    "Blurry photos",
    PROCESSING_FAILURE_FILTER,
    "Duplicate groups",
    "Photos with faces",
  ]);
});

test("recognizes supported review filter values", () => {
  assert.equal(isReviewFilter("Picks"), true);
  assert.equal(isReviewFilter(PROCESSING_FAILURE_FILTER), true);
  assert.equal(isReviewFilter("Missing"), false);
  assert.equal(isReviewFilter(null), false);
});

test("matches user status filters", () => {
  assert.equal(photoMatchesReviewFilter(photo({ user_status: "Pick" }), "Picks", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ user_status: "Maybe" }), "Maybes", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ user_status: "Reject" }), "Rejects", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ user_status: "Unreviewed" }), "Unreviewed", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ user_status: "Maybe" }), "Picks", new Set()), false);
});

test("matches recommendation and technical filters", () => {
  assert.equal(photoMatchesReviewFilter(photo({ ai_recommendation: "Pick" }), "AI recommended", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ ai_recommendation: "Maybe" }), "AI recommended", new Set()), false);
  assert.equal(photoMatchesReviewFilter(photo({ blur_score: 0.55 }), "Blurry photos", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ blur_score: 0.54 }), "Blurry photos", new Set()), false);
  assert.equal(photoMatchesReviewFilter(photo({ face_presence: true }), "Photos with faces", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ face_presence: false }), "Photos with faces", new Set()), false);
});

test("matches processing failures from state or error text", () => {
  assert.equal(
    photoMatchesReviewFilter(photo({ processing_state: "failed" }), PROCESSING_FAILURE_FILTER, new Set()),
    true,
  );
  assert.equal(
    photoMatchesReviewFilter(photo({ processing_error: "Missing generated preview" }), PROCESSING_FAILURE_FILTER, new Set()),
    true,
  );
  assert.equal(photoMatchesReviewFilter(photo(), PROCESSING_FAILURE_FILTER, new Set()), false);
});

test("matches duplicate groups from known duplicate group ids", () => {
  const duplicateGroupIds = new Set(["group-duplicate"]);

  assert.equal(photoMatchesReviewFilter(photo({ group_id: "group-duplicate" }), "Duplicate groups", duplicateGroupIds), true);
  assert.equal(photoMatchesReviewFilter(photo({ group_id: "group-single" }), "Duplicate groups", duplicateGroupIds), false);
  assert.equal(photoMatchesReviewFilter(photo({ group_id: null }), "Duplicate groups", duplicateGroupIds), false);
});

test("matches all photos for all or unknown filters", () => {
  assert.equal(photoMatchesReviewFilter(photo({ user_status: "Reject" }), "All", new Set()), true);
  assert.equal(photoMatchesReviewFilter(photo({ user_status: "Reject" }), "Unknown", new Set()), true);
});
