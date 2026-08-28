import assert from "node:assert/strict";
import test from "node:test";
import { maxRenderedVirtualItems } from "./virtualRenderBudget.ts";

test("virtual render budget stays far below a 2k workspace list", () => {
  const filmstripBudget = maxRenderedVirtualItems({
    itemCount: 2000,
    viewportSize: 960,
    estimateSize: 120,
    overscan: 6,
  });
  const groupBudget = maxRenderedVirtualItems({
    itemCount: 2000,
    viewportSize: 720,
    estimateSize: 64,
    overscan: 8,
  });

  assert.equal(filmstripBudget, 20);
  assert.equal(groupBudget, 28);
  assert.ok(filmstripBudget < 2000 * 0.05);
  assert.ok(groupBudget < 2000 * 0.05);
});

test("virtual render budget never exceeds the item count", () => {
  assert.equal(
    maxRenderedVirtualItems({ itemCount: 3, viewportSize: 960, estimateSize: 120, overscan: 6 }),
    3,
  );
  assert.equal(
    maxRenderedVirtualItems({ itemCount: 0, viewportSize: 960, estimateSize: 120, overscan: 6 }),
    0,
  );
});

test("dom budget for 2000 items stays under an interaction-friendly ceiling", () => {
  const budget = maxRenderedVirtualItems({
    itemCount: 2000,
    viewportSize: 1280,
    estimateSize: 120,
    overscan: 6,
  });
  assert.ok(budget <= 32);
  assert.ok(budget < 50);
});
