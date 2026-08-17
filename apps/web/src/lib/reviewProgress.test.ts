import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_REVIEW_PROGRESS,
  normalizeReviewProgress,
  parseReviewProgress,
  reviewProgressAfterFilterChange,
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
        previewZoom: 1.5,
      }),
      filters,
    ),
    {
      activeGroupId: "group-1",
      activePhotoId: "photo-1",
      compareMode: true,
      filter: "Picks",
      largePreview: true,
      previewZoom: 1.5,
    },
  );
});

test("falls back for malformed review progress", () => {
  assert.deepEqual(parseReviewProgress("not json", filters), DEFAULT_REVIEW_PROGRESS);
  assert.deepEqual(parseReviewProgress(null, filters), DEFAULT_REVIEW_PROGRESS);
});

test("normalizes partial, stale, or legacy review progress", () => {
  assert.deepEqual(normalizeReviewProgress({ activePhotoId: 7, filter: "Missing", zoomPreview: true }, filters), {
    activeGroupId: null,
    activePhotoId: null,
    compareMode: false,
    filter: "All",
    largePreview: false,
    previewZoom: 1,
  });
});

test("clamps stored preview zoom to the supported range", () => {
  assert.equal(normalizeReviewProgress({ previewZoom: 8 }, filters).previewZoom, 4);
  assert.equal(normalizeReviewProgress({ previewZoom: 0.1 }, filters).previewZoom, 0.25);
  assert.equal(normalizeReviewProgress({ previewZoom: "2" }, filters).previewZoom, 1);
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
        previewZoom: 1.25,
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
      previewZoom: 1.25,
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
    previewZoom: 1.25,
  });

  assert.deepEqual(reviewProgressForEntry(stored, filters, "Missing"), {
    activeGroupId: "group-1",
    activePhotoId: "photo-1",
    compareMode: true,
    filter: "Picks",
    largePreview: true,
    previewZoom: 1.25,
  });
  assert.deepEqual(reviewProgressForEntry(stored, filters, null), {
    activeGroupId: "group-1",
    activePhotoId: "photo-1",
    compareMode: true,
    filter: "Picks",
    largePreview: true,
    previewZoom: 1.25,
  });
});

test("applies requested review filters to fallback entry progress", () => {
  assert.deepEqual(reviewProgressForEntry("not json", filters, "Maybes"), {
    ...DEFAULT_REVIEW_PROGRESS,
    filter: "Maybes",
  });
});

test("clears active selection when changing review filters", () => {
  assert.deepEqual(
    reviewProgressAfterFilterChange(
      {
        activeGroupId: "group-1",
        activePhotoId: "photo-1",
        compareMode: true,
        filter: "Picks",
        largePreview: true,
        previewZoom: 1.25,
      },
      "Maybes",
    ),
    {
      activeGroupId: null,
      activePhotoId: null,
      compareMode: true,
      filter: "Maybes",
      largePreview: true,
      previewZoom: 1.25,
    },
  );
});
