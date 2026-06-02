import test from "node:test";
import assert from "node:assert/strict";

import { nextPhotoIdAfterMark, type ReviewPhotoRef } from "./reviewNavigation.ts";

const photos: ReviewPhotoRef[] = [{ id: "first" }, { id: "second" }, { id: "third" }];

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
