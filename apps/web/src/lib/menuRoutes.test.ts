import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";

import { MENU_EVENT, MENU_ITEMS, menuHrefForCommand } from "./menuRoutes.ts";

test("defines File Edit View Project Help native menu items", () => {
  assert.deepEqual(Object.keys(MENU_ITEMS), ["File", "Edit", "View", "Project", "Help"]);
  assert.deepEqual(
    MENU_ITEMS.File.map((item) => item.id),
    ["new", "open-data-folder", "import", "export", "close", "quit"],
  );
  assert.deepEqual(
    MENU_ITEMS.File.map((item) => item.label),
    ["New", "Open data folder", "Import", "Export", "Close", "Quit"],
  );
  assert.deepEqual(
    MENU_ITEMS.Edit.map((item) => item.id),
    ["undo", "redo", "cut", "copy", "paste", "select_all"],
  );
  assert.deepEqual(
    MENU_ITEMS.View.map((item) => item.id),
    ["fullscreen"],
  );
  assert.deepEqual(MENU_ITEMS.View.map((item) => item.label), ["Fullscreen"]);
  assert.deepEqual(
    MENU_ITEMS.Project.map((item) => item.id),
    ["process", "cull"],
  );
  assert.deepEqual(MENU_ITEMS.Project.map((item) => item.label), ["Process", "Culling"]);
  assert.deepEqual(
    MENU_ITEMS.Help.map((item) => item.id),
    ["shortcuts", "about"],
  );
  assert.deepEqual(MENU_ITEMS.Help.map((item) => item.label), ["Shortcuts", "About"]);
  assert.equal(MENU_EVENT, "framepilot-menu");
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

test("leaves native-only menu commands without a route", () => {
  assert.equal(menuHrefForCommand("open-data-folder", "/projects/abc", "abc"), null);
  assert.equal(menuHrefForCommand("close", "/projects/abc", "abc"), null);
  assert.equal(menuHrefForCommand("quit", "/projects/abc", "abc"), null);
  assert.equal(menuHrefForCommand("fullscreen", "/projects/abc", "abc"), null);
  assert.equal(menuHrefForCommand("about", "/projects/abc", "abc"), null);
});

test("does not bind reserved culling keys as bare accelerators", () => {
  const reserved = new Set(["p", "m", "x", "u", "1", "2", "3", "4", "5", "0", " ", "z", "c", "g", "f", "e", "space"]);
  const items = Object.values(MENU_ITEMS).flat();
  for (const item of items) {
    const accelerator = item.accelerator;
    if (!accelerator) {
      continue;
    }
    const parts = accelerator.split("+");
    const last = parts[parts.length - 1]?.toLowerCase() ?? "";
    if (parts.length === 1) {
      assert.equal(reserved.has(last), false, `${item.id} uses reserved bare accelerator ${accelerator}`);
    }
  }
});

test("rust menu source avoids reserved bare-key accelerators", () => {
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
});
