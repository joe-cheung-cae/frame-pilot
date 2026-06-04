import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_REVIEW_PROGRESS,
  normalizeReviewProgress,
  parseReviewProgress,
  reviewProgressForEntry,
  reviewProgressStorageKey,
} from "./reviewProgress.ts";

const filters = ["All", "Picks", "Maybes"];

test("builds project-specific review progress storage keys", () => {
  assert.equal(reviewProgressStorageKey("project-1"), "framepilot.reviewProgress.v1.project-1");
});

test("parses stored review progress", () => {
  assert.deepEqual(
    parseReviewProgress(
      JSON.stringify({
        activeGroupId: "group-1",
        activePhotoId: "photo-1",
        compareMode: true,
        filter: "Picks",
        largePreview: true,
        zoomPreview: true,
      }),
      filters,
    ),
    {
      activeGroupId: "group-1",
      activePhotoId: "photo-1",
      compareMode: true,
      filter: "Picks",
      largePreview: true,
      zoomPreview: true,
    },
  );
});

test("falls back for malformed review progress", () => {
  assert.deepEqual(parseReviewProgress("not json", filters), DEFAULT_REVIEW_PROGRESS);
  assert.deepEqual(parseReviewProgress(null, filters), DEFAULT_REVIEW_PROGRESS);
});

test("normalizes partial or stale review progress", () => {
  assert.deepEqual(normalizeReviewProgress({ activePhotoId: 7, filter: "Missing", zoomPreview: true }, filters), {
    activeGroupId: null,
    activePhotoId: null,
    compareMode: false,
    filter: "All",
    largePreview: false,
    zoomPreview: true,
  });
});

test("uses valid requested filters for review entry progress", () => {
  assert.deepEqual(
    reviewProgressForEntry(
      JSON.stringify({
        activeGroupId: "group-1",
        activePhotoId: "photo-1",
        compareMode: true,
        filter: "Picks",
        largePreview: true,
        zoomPreview: true,
      }),
      filters,
      "Maybes",
    ),
    {
      activeGroupId: null,
      activePhotoId: null,
      compareMode: true,
      filter: "Maybes",
      largePreview: true,
      zoomPreview: true,
    },
  );
});

test("preserves stored review entry progress without a valid requested filter", () => {
  const stored = JSON.stringify({
    activeGroupId: "group-1",
    activePhotoId: "photo-1",
    compareMode: true,
    filter: "Picks",
    largePreview: true,
    zoomPreview: true,
  });

  assert.deepEqual(reviewProgressForEntry(stored, filters, "Missing"), {
    activeGroupId: "group-1",
    activePhotoId: "photo-1",
    compareMode: true,
    filter: "Picks",
    largePreview: true,
    zoomPreview: true,
  });
  assert.deepEqual(reviewProgressForEntry(stored, filters, null), {
    activeGroupId: "group-1",
    activePhotoId: "photo-1",
    compareMode: true,
    filter: "Picks",
    largePreview: true,
    zoomPreview: true,
  });
});

test("applies requested review filters to fallback entry progress", () => {
  assert.deepEqual(reviewProgressForEntry("not json", filters, "Maybes"), {
    ...DEFAULT_REVIEW_PROGRESS,
    filter: "Maybes",
  });
});
