import test from "node:test";
import assert from "node:assert/strict";

import {
  groupAfterMove,
  nextPhotoIdAfterMark,
  windowedPhotoRefs,
  type ReviewGroupRef,
  type ReviewPhotoRef,
} from "./reviewNavigation.ts";

const photos: ReviewPhotoRef[] = [{ id: "first" }, { id: "second" }, { id: "third" }];
const groups: ReviewGroupRef[] = [
  { id: "group-1", representative_photo_id: "first" },
  { id: "group-2", representative_photo_id: "second" },
  { id: "group-3", representative_photo_id: null },
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
