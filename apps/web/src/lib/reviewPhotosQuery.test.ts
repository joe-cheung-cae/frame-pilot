import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { photosQueryKey } from "./reviewPhotosQuery.ts";

describe("photosQueryKey", () => {
  it("uses distinct keys for page vs full load so refetch cannot mix modes", () => {
    assert.deepEqual(photosQueryKey("p1", false), ["photos", "p1", "page"]);
    assert.deepEqual(photosQueryKey("p1", true), ["photos", "p1", "all"]);
    assert.notDeepEqual(photosQueryKey("p1", false), photosQueryKey("p1", true));
  });
});
