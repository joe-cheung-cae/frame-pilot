import test from "node:test";
import assert from "node:assert/strict";

import { projectNextHref } from "./projectRouting.ts";

test("routes empty projects to import", () => {
  assert.equal(projectNextHref({ id: "p1", total_images: 0, processed_images: 0 }), "/projects/p1/import");
});

test("routes imported but unprocessed projects to processing", () => {
  assert.equal(projectNextHref({ id: "p1", total_images: 3, processed_images: 0 }), "/projects/p1/process");
});

test("routes processed projects to culling", () => {
  assert.equal(projectNextHref({ id: "p1", total_images: 3, processed_images: 3 }), "/projects/p1/cull");
});
