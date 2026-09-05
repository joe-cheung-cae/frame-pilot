import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";

import {
  MENU_EVENT,
  desktopMenuHelpSection,
  menuHrefForCommand,
  resolveMenuCommand,
} from "./menuRoutes.ts";
import { projectIdFromPathname } from "./projectRouting.ts";

const NAVIGABLE = ["new", "shortcuts", "import", "export", "process", "cull"] as const;
const NATIVE_OWNED = [
  "open-data-folder",
  "close",
  "quit",
  "fullscreen",
  "detached-preview",
  "about",
  "undo",
  "redo",
  "cut",
  "copy",
  "paste",
  "select_all",
] as const;

test("TypeScript resolves only navigable menu commands", () => {
  const source = fs.readFileSync(new URL("./menuRoutes.ts", import.meta.url), "utf8");
  assert.doesNotMatch(source, /export const MENU_ITEMS/);
  assert.doesNotMatch(source, /menuNativeAction/);
  assert.equal(MENU_EVENT, "framepilot-menu");
  for (const id of NAVIGABLE) {
    const resolved = resolveMenuCommand(id, "/projects/abc/cull", "abc");
    assert.equal(resolved.type, "navigate");
    assert.ok(resolved.href);
  }
});

test("native-owned menu ids are ignored by JS routing", () => {
  for (const id of NATIVE_OWNED) {
    assert.equal(menuHrefForCommand(id, "/projects/abc", "abc"), null);
    assert.deepEqual(resolveMenuCommand(id, "/projects/abc", "abc"), { type: "ignore" });
  }
});

test("routes New and Shortcuts without a project id", () => {
  assert.equal(menuHrefForCommand("new", "/", null), "/projects/new");
  assert.equal(menuHrefForCommand("shortcuts", "/projects/abc/cull", "abc"), "/help");
});

test("routes Import Export Process Culling from the current project path", () => {
  assert.equal(menuHrefForCommand("import", "/projects/abc", null), "/projects/abc/import");
  assert.equal(menuHrefForCommand("export", "/projects/abc/cull", null), "/projects/abc/export");
  assert.equal(menuHrefForCommand("process", "/projects/abc/import", null), "/projects/abc/process");
  assert.equal(menuHrefForCommand("cull", "/projects/abc/export", null), "/projects/abc/cull");
});

test("ignores the new-project path and uses last opened project id", () => {
  assert.equal(menuHrefForCommand("import", "/projects/new", "last-id"), "/projects/last-id/import");
  assert.equal(menuHrefForCommand("cull", "/", "last-id"), "/projects/last-id/cull");
  assert.equal(menuHrefForCommand("process", "/help", null), null);
  assert.equal(menuHrefForCommand("export", "/projects/new", null), null);
});

test("projectIdFromPathname is a generic path helper", () => {
  assert.equal(projectIdFromPathname("/projects/abc/cull"), "abc");
  assert.equal(projectIdFromPathname("/projects/new"), null);
  assert.equal(projectIdFromPathname("/help"), null);
  const menuSource = fs.readFileSync(new URL("./menuRoutes.ts", import.meta.url), "utf8");
  assert.doesNotMatch(menuSource, /export function projectIdFromPathname/);
});

test("Help documents only CmdOrCtrl+N/W/Q from the desktop menu", () => {
  assert.deepEqual(
    desktopMenuHelpSection.shortcuts.map((item) => item.keys),
    ["CmdOrCtrl+N", "CmdOrCtrl+W", "CmdOrCtrl+Q"],
  );
  const help = fs.readFileSync(new URL("../components/HelpShortcuts.tsx", import.meta.url), "utf8");
  assert.match(help, /desktopMenuHelpSection/);
});

test("rust menu source remains the native catalog and avoids reserved bare-key accelerators", () => {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const menuSourcePath = path.resolve(here, "../../../desktop/src-tauri/src/menu.rs");
  const source = fs.readFileSync(menuSourcePath, "utf8");
  assert.match(source, /"File"/);
  assert.match(source, /"Edit"/);
  assert.match(source, /"View"/);
  assert.match(source, /"Project"/);
  assert.match(source, /"Help"/);
  for (const key of ["P", "M", "X", "U", "1", "2", "3", "4", "5", "0", "Space", "Z", "C", "G", "F", "E"]) {
    assert.doesNotMatch(
      source,
      new RegExp(String.raw`accelerator\("${key}"\)`),
      `menu.rs must not use bare accelerator ${key}`,
    );
    if (/^[A-Z]$/.test(key)) {
      assert.doesNotMatch(source, new RegExp(String.raw`accelerator\("${key.toLowerCase()}"\)`));
    }
  }
  assert.match(source, /with_id\("detached-preview", "Detached preview"\)/);
  const detachedIndex = source.indexOf('with_id("detached-preview"');
  assert.notEqual(detachedIndex, -1);
  const detachedSlice = source.slice(detachedIndex, detachedIndex + 180);
  assert.doesNotMatch(detachedSlice, /accelerator/);
});
