import test from "node:test";
import assert from "node:assert/strict";

import {
  REVIEW_SHORTCUT_HELP_SECTIONS,
  reviewShortcutCommandForKey,
  reviewShortcutNeedsPreventDefault,
} from "./reviewShortcuts.ts";

test("maps photo and group navigation shortcuts", () => {
  assert.deepEqual(reviewShortcutCommandForKey("ArrowLeft"), { type: "move_photo", delta: -1 });
  assert.deepEqual(reviewShortcutCommandForKey("ArrowRight"), { type: "move_photo", delta: 1 });
  assert.deepEqual(reviewShortcutCommandForKey("ArrowUp"), { type: "move_group", delta: -1 });
  assert.deepEqual(reviewShortcutCommandForKey("ArrowDown"), { type: "move_group", delta: 1 });
});

test("maps status shortcuts case-insensitively", () => {
  assert.deepEqual(reviewShortcutCommandForKey("p"), { type: "mark", status: "Pick" });
  assert.deepEqual(reviewShortcutCommandForKey("M"), { type: "mark", status: "Maybe" });
  assert.deepEqual(reviewShortcutCommandForKey("x"), { type: "mark", status: "Reject" });
  assert.deepEqual(reviewShortcutCommandForKey("U"), { type: "mark", status: "Unreviewed" });
});

test("maps rating shortcuts including clear rating", () => {
  assert.deepEqual(reviewShortcutCommandForKey("0"), { type: "rate", rating: 0 });
  assert.deepEqual(reviewShortcutCommandForKey("1"), { type: "rate", rating: 1 });
  assert.deepEqual(reviewShortcutCommandForKey("5"), { type: "rate", rating: 5 });
  assert.equal(reviewShortcutCommandForKey("6"), null);
});

test("maps workspace mode and routing shortcuts", () => {
  assert.deepEqual(reviewShortcutCommandForKey(" "), { type: "toggle_large_preview" });
  assert.deepEqual(reviewShortcutCommandForKey("z"), { type: "toggle_zoom" });
  assert.deepEqual(reviewShortcutCommandForKey("C"), { type: "toggle_compare" });
  assert.deepEqual(reviewShortcutCommandForKey("g"), { type: "cycle_group" });
  assert.deepEqual(reviewShortcutCommandForKey("F"), { type: "focus_filters" });
  assert.deepEqual(reviewShortcutCommandForKey("e"), { type: "export" });
  assert.equal(reviewShortcutCommandForKey("Escape"), null);
});

test("prevents browser defaults only for scrolling shortcuts", () => {
  assert.equal(reviewShortcutNeedsPreventDefault({ type: "move_group", delta: 1 }), true);
  assert.equal(reviewShortcutNeedsPreventDefault({ type: "toggle_large_preview" }), true);
  assert.equal(reviewShortcutNeedsPreventDefault({ type: "move_photo", delta: 1 }), false);
  assert.equal(reviewShortcutNeedsPreventDefault({ type: "export" }), false);
});

test("documents shortcuts by culling workflow section", () => {
  assert.deepEqual(
    REVIEW_SHORTCUT_HELP_SECTIONS.map((section) => section.title),
    ["Navigation", "Review", "Workspace"],
  );
  assert.deepEqual(
    REVIEW_SHORTCUT_HELP_SECTIONS.flatMap((section) =>
      section.shortcuts.map((shortcut) => `${shortcut.keys}: ${shortcut.action}`),
    ),
    [
      "Left Arrow: Previous photo",
      "Right Arrow: Next photo",
      "Up Arrow: Previous group",
      "Down Arrow: Next group",
      "P: Mark Pick",
      "M: Mark Maybe",
      "X: Mark Reject",
      "U: Mark Unreviewed",
      "1 to 5: Set star rating",
      "0: Clear star rating",
      "Space: Toggle large preview",
      "Z: Toggle zoom",
      "C: Toggle compare",
      "G: Cycle group selection",
      "F: Focus filter menu",
      "E: Open export",
    ],
  );
});
