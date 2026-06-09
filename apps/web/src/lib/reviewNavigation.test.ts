import test from "node:test";
import assert from "node:assert/strict";

import {
  groupAfterMove,
  nextPhotoIdAfterMark,
  reviewAssetFallbackMessage,
  reviewBatchScopeDetail,
  reviewBatchScopeSummary,
  reviewEmptyStateMessage,
  reviewLoadRecoveryMessage,
  reviewSaveFailureMessage,
  reviewSelectionState,
  windowedCompareRefs,
  windowedGroupRefs,
  windowedPhotoRefs,
  type ReviewGroupedPhotoRef,
  type ReviewGroupRef,
  type ReviewPhotoRef,
} from "./reviewNavigation.ts";

const photos: ReviewPhotoRef[] = [{ id: "first" }, { id: "second" }, { id: "third" }];
const groups: ReviewGroupRef[] = [
  { id: "group-1", representative_photo_id: "first" },
  { id: "group-2", representative_photo_id: "second" },
  { id: "group-3", representative_photo_id: null },
];
const groupedPhotos: ReviewGroupedPhotoRef[] = [
  { id: "first", group_id: "group-1" },
  { id: "second", group_id: "group-1" },
  { id: "third", group_id: "group-2" },
  { id: "ungrouped", group_id: null },
];

test("advances to the next visible photo after marking", () => {
  assert.equal(nextPhotoIdAfterMark(photos, "first"), "second");
});

test("falls back to the previous visible photo after marking the last item", () => {
  assert.equal(nextPhotoIdAfterMark(photos, "third"), "second");
});

test("keeps the only visible photo selected after marking", () => {
  assert.equal(nextPhotoIdAfterMark([{ id: "only" }], "only"), "only");
});

test("advances from the first visible slot when the active photo is missing", () => {
  assert.equal(nextPhotoIdAfterMark(photos, "missing"), "second");
});

test("returns null when there are no visible photos", () => {
  assert.equal(nextPhotoIdAfterMark([], "missing"), null);
});

test("moves to the next group from the active group", () => {
  assert.deepEqual(groupAfterMove(groups, "group-1", 1), groups[1]);
});

test("moves to the previous group from the active group", () => {
  assert.deepEqual(groupAfterMove(groups, "group-2", -1), groups[0]);
});

test("keeps group navigation inside available groups", () => {
  assert.deepEqual(groupAfterMove(groups, "group-1", -1), groups[0]);
  assert.deepEqual(groupAfterMove(groups, "group-3", 1), groups[2]);
});

test("starts group navigation from the first group when no group is active", () => {
  assert.deepEqual(groupAfterMove(groups, null, 1), groups[0]);
  assert.deepEqual(groupAfterMove(groups, null, -1), groups[0]);
});

test("returns null when there are no groups", () => {
  assert.equal(groupAfterMove([], "missing", 1), null);
});

test("resolves active review selection from visible photos", () => {
  assert.deepEqual(
    reviewSelectionState({
      activeGroupId: null,
      activePhotoId: "second",
      filteredPhotos: groupedPhotos,
      groups,
      visiblePhotos: groupedPhotos,
    }),
    {
      activeGroup: groups[0],
      activeIndex: 1,
      activePhoto: groupedPhotos[1],
      compareCandidates: groupedPhotos.slice(0, 2),
    },
  );
});

test("falls back to the first visible photo for stale active review selections", () => {
  assert.deepEqual(
    reviewSelectionState({
      activeGroupId: null,
      activePhotoId: "missing",
      filteredPhotos: groupedPhotos,
      groups,
      visiblePhotos: groupedPhotos,
    }),
    {
      activeGroup: groups[0],
      activeIndex: 0,
      activePhoto: groupedPhotos[0],
      compareCandidates: groupedPhotos.slice(0, 2),
    },
  );
});

test("keeps a selected group when the current filter hides its photos", () => {
  assert.deepEqual(
    reviewSelectionState({
      activeGroupId: "group-2",
      activePhotoId: "third",
      filteredPhotos: groupedPhotos.slice(0, 2),
      groups,
      visiblePhotos: [],
    }),
    {
      activeGroup: groups[1],
      activeIndex: 0,
      activePhoto: null,
      compareCandidates: [],
    },
  );
});

test("uses the active photo as the only compare candidate without an active group", () => {
  assert.deepEqual(
    reviewSelectionState({
      activeGroupId: null,
      activePhotoId: "ungrouped",
      filteredPhotos: groupedPhotos,
      groups,
      visiblePhotos: groupedPhotos,
    }),
    {
      activeGroup: null,
      activeIndex: 3,
      activePhoto: groupedPhotos[3],
      compareCandidates: [groupedPhotos[3]],
    },
  );
});

test("summarizes batch scope for all loaded photos", () => {
  assert.equal(
    reviewBatchScopeSummary({ activeGroupIndex: -1, filter: "All", visiblePhotoCount: 42 }),
    "42 photos",
  );
  assert.equal(
    reviewBatchScopeDetail({
      activeGroupIndex: -1,
      filter: "All",
      loadedPhotoCount: 42,
      photosPartiallyLoaded: false,
      projectPhotoCount: 42,
      visiblePhotoCount: 42,
    }),
    "Applies to all 42 photos currently loaded.",
  );
});

test("explains filtered batch scope", () => {
  assert.equal(
    reviewBatchScopeSummary({ activeGroupIndex: -1, filter: "Pick", visiblePhotoCount: 3 }),
    "Pick · 3 photos",
  );
  assert.equal(
    reviewBatchScopeDetail({
      activeGroupIndex: -1,
      filter: "Pick",
      loadedPhotoCount: 20,
      photosPartiallyLoaded: false,
      projectPhotoCount: 20,
      visiblePhotoCount: 3,
    }),
    "Applies only to loaded photos matching Pick.",
  );
});

test("explains group batch scope with partial loading", () => {
  assert.equal(
    reviewBatchScopeSummary({ activeGroupIndex: 1, filter: "Maybe", visiblePhotoCount: 2 }),
    "Group 2 · 2 photos",
  );
  assert.equal(
    reviewBatchScopeDetail({
      activeGroupIndex: 1,
      filter: "Maybe",
      loadedPhotoCount: 500,
      photosPartiallyLoaded: true,
      projectPhotoCount: 900,
      visiblePhotoCount: 2,
    }),
    "Applies only to loaded photos in Group 2 matching Maybe. Load all photos before batch marking if you need the full project of 900 photos.",
  );
});

test("explains empty batch scope", () => {
  assert.equal(
    reviewBatchScopeSummary({ activeGroupIndex: -1, filter: "Reject", visiblePhotoCount: 0 }),
    "Reject · 0 photos",
  );
  assert.equal(
    reviewBatchScopeDetail({
      activeGroupIndex: -1,
      filter: "Reject",
      loadedPhotoCount: 12,
      photosPartiallyLoaded: false,
      projectPhotoCount: 12,
      visiblePhotoCount: 0,
    }),
    "No loaded photos match the Reject filter.",
  );
  assert.equal(
    reviewBatchScopeDetail({
      activeGroupIndex: 0,
      filter: "All",
      loadedPhotoCount: 12,
      photosPartiallyLoaded: false,
      projectPhotoCount: 12,
      visiblePhotoCount: 0,
    }),
    "No loaded photos are available in this group.",
  );
});

test("explains empty batch scope with partial loading", () => {
  assert.equal(
    reviewBatchScopeDetail({
      activeGroupIndex: -1,
      filter: "Pick",
      loadedPhotoCount: 500,
      photosPartiallyLoaded: true,
      projectPhotoCount: 1200,
      visiblePhotoCount: 0,
    }),
    "No loaded photos match the Pick filter. Load all photos before batch marking if you need the full project of 1200 photos.",
  );
});

test("explains empty review states for fully loaded photos", () => {
  assert.deepEqual(
    reviewEmptyStateMessage({
      filter: "Rejects",
      hasActiveGroup: false,
      loadedPhotoCount: 12,
      photosPartiallyLoaded: false,
      projectPhotoCount: 12,
    }),
    {
      detail: "",
      title: "No photos match the Rejects filter.",
    },
  );
  assert.deepEqual(
    reviewEmptyStateMessage({
      filter: "All",
      hasActiveGroup: true,
      loadedPhotoCount: 12,
      photosPartiallyLoaded: false,
      projectPhotoCount: 12,
    }),
    {
      detail: "",
      title: "No photos in this group are available.",
    },
  );
});

test("explains empty review states for partially loaded photos", () => {
  assert.deepEqual(
    reviewEmptyStateMessage({
      filter: "Maybes",
      hasActiveGroup: false,
      loadedPhotoCount: 500,
      photosPartiallyLoaded: true,
      projectPhotoCount: 1200,
    }),
    {
      detail: "Only 500 of 1200 photos are loaded.",
      title: "No loaded photos match the Maybes filter.",
    },
  );
  assert.deepEqual(
    reviewEmptyStateMessage({
      filter: "All",
      hasActiveGroup: true,
      loadedPhotoCount: 500,
      photosPartiallyLoaded: true,
      projectPhotoCount: 1200,
    }),
    {
      detail: "Only 500 of 1200 photos are loaded.",
      title: "No loaded photos in this group are available.",
    },
  );
});

test("uses singular grammar for partially loaded one-photo projects", () => {
  assert.deepEqual(
    reviewEmptyStateMessage({
      filter: "All",
      hasActiveGroup: false,
      loadedPhotoCount: 0,
      photosPartiallyLoaded: true,
      projectPhotoCount: 1,
    }),
    {
      detail: "Only 0 of 1 photo is loaded.",
      title: "No loaded photos are available.",
    },
  );
});

test("explains save failures after optimistic review updates roll back", () => {
  assert.equal(
    reviewSaveFailureMessage({ errorMessage: "Network error", isBatch: false }),
    "Photo update could not be saved. The visible status has been restored. Network error",
  );
  assert.equal(
    reviewSaveFailureMessage({ errorMessage: "API unavailable", isBatch: true }),
    "Batch update could not be saved. The visible status has been restored. API unavailable",
  );
});

test("explains local preview fallback states", () => {
  assert.deepEqual(reviewAssetFallbackMessage({ assetType: "preview", hasAssetUrl: true }), {
    detail: "The original file remains unchanged. Reopen the project or rerun local processing to regenerate previews.",
    shortTitle: "Preview failed",
    title: "Local preview failed to load.",
  });
  assert.deepEqual(reviewAssetFallbackMessage({ assetType: "preview", hasAssetUrl: false }), {
    detail: "Run import or processing again to create a local preview without modifying the original file.",
    shortTitle: "No preview",
    title: "No local preview is available.",
  });
});

test("explains local thumbnail fallback states", () => {
  assert.deepEqual(reviewAssetFallbackMessage({ assetType: "thumbnail", hasAssetUrl: true }), {
    detail: "The generated local thumbnail could not load.",
    shortTitle: "Thumbnail failed",
    title: "Local thumbnail failed to load.",
  });
  assert.deepEqual(reviewAssetFallbackMessage({ assetType: "thumbnail", hasAssetUrl: false }), {
    detail: "No generated local thumbnail is available for this photo.",
    shortTitle: "No thumbnail",
    title: "No local thumbnail is available.",
  });
});

test("explains how to recover from culling data load failures", () => {
  assert.equal(
    reviewLoadRecoveryMessage("workspace"),
    "Confirm the local FramePilot API is running, then reload the culling workspace. Original photos remain unchanged.",
  );
  assert.equal(
    reviewLoadRecoveryMessage("photos"),
    "Confirm the local FramePilot API is running, then load all photos again. Review status changes already saved stay in the local project database.",
  );
  assert.equal(
    reviewLoadRecoveryMessage("groups"),
    "Confirm the local FramePilot API is running, then load all groups again. Existing grouping metadata stays in the local project database.",
  );
});

test("returns every photo when the filmstrip fits inside the window", () => {
  assert.deepEqual(windowedPhotoRefs(photos, "second", 5), photos);
});

test("windows filmstrip photos around the active photo", () => {
  const manyPhotos = Array.from({ length: 10 }, (_value, index) => ({ id: `photo-${index}` }));

  assert.deepEqual(
    windowedPhotoRefs(manyPhotos, "photo-5", 4).map((photo) => photo.id),
    ["photo-3", "photo-4", "photo-5", "photo-6"],
  );
});

test("keeps filmstrip windows inside the available photo range", () => {
  const manyPhotos = Array.from({ length: 10 }, (_value, index) => ({ id: `photo-${index}` }));

  assert.deepEqual(
    windowedPhotoRefs(manyPhotos, "photo-0", 4).map((photo) => photo.id),
    ["photo-0", "photo-1", "photo-2", "photo-3"],
  );
  assert.deepEqual(
    windowedPhotoRefs(manyPhotos, "photo-9", 4).map((photo) => photo.id),
    ["photo-6", "photo-7", "photo-8", "photo-9"],
  );
});

test("windows group refs around the active group", () => {
  const manyGroups = Array.from({ length: 10 }, (_value, index) => ({
    id: `group-${index}`,
    representative_photo_id: null,
  }));

  assert.deepEqual(
    windowedGroupRefs(manyGroups, "group-5", 4).map((group) => group.id),
    ["group-3", "group-4", "group-5", "group-6"],
  );
});

test("keeps group windows inside the available group range", () => {
  const manyGroups = Array.from({ length: 10 }, (_value, index) => ({
    id: `group-${index}`,
    representative_photo_id: null,
  }));

  assert.deepEqual(
    windowedGroupRefs(manyGroups, "group-0", 4).map((group) => group.id),
    ["group-0", "group-1", "group-2", "group-3"],
  );
  assert.deepEqual(
    windowedGroupRefs(manyGroups, "group-9", 4).map((group) => group.id),
    ["group-6", "group-7", "group-8", "group-9"],
  );
});

test("windows compare refs for large duplicate groups", () => {
  const manyPhotos = Array.from({ length: 2000 }, (_value, index) => ({ id: `photo-${index}` }));

  assert.deepEqual(
    windowedCompareRefs(manyPhotos, "photo-1000", 6).map((photo) => photo.id),
    ["photo-997", "photo-998", "photo-999", "photo-1000", "photo-1001", "photo-1002"],
  );
});
