import test from "node:test";
import assert from "node:assert/strict";

import { desktopSystemDarkMode } from "../theme/darkMode.ts";
import { colorHex } from "../theme/tokens.ts";

test("Tailwind dark variant is scoped to desktop shell and system dark preference", () => {
  assert.equal(desktopSystemDarkMode[0], "variant");
  const variants = desktopSystemDarkMode[1];
  assert.ok(Array.isArray(variants) && variants.length >= 1);
  for (const variant of variants) {
    assert.match(variant, /prefers-color-scheme:\s*dark/);
    assert.match(variant, /\[data-shell="desktop"\]/);
    assert.doesNotMatch(variant, /\[data-shell="browser"\]/);
  }
});

test("light palette hex tokens stay the FramePilot light look", () => {
  assert.equal(colorHex.ink, "#151515");
  assert.equal(colorHex.mist, "#f5f7f8");
  assert.equal(colorHex.line, "#d8dedc");
  assert.equal(colorHex.leaf, "#2f6f5e");
  assert.equal(colorHex.coral, "#bf5b45");
  assert.equal(colorHex.gold, "#a77721");
  assert.equal(colorHex.paper, "#ffffff");
});
