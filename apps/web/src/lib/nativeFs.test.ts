import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";

import { getNativeFs } from "./nativeFs.ts";

type TestWindow = {
  __FRAMEPILOT_DESKTOP__?: unknown;
};

const here = path.dirname(fileURLToPath(import.meta.url));
const webSrc = path.resolve(here, "..");
const appsRoot = path.resolve(here, "../../..");
const capabilitiesPath = path.resolve(appsRoot, "desktop/src-tauri/capabilities/default.json");

function withWindow<T>(windowValue: TestWindow | undefined, run: () => T): T {
  const globalObject = globalThis as { window?: TestWindow };
  const hadWindow = Object.prototype.hasOwnProperty.call(globalThis, "window");
  const previous = globalObject.window;
  if (windowValue === undefined) {
    delete globalObject.window;
  } else {
    globalObject.window = windowValue;
  }
  try {
    return run();
  } finally {
    if (hadWindow) {
      globalObject.window = previous;
    } else {
      delete globalObject.window;
    }
  }
}

function listSourceFiles(dir: string): string[] {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...listSourceFiles(fullPath));
      continue;
    }
    if (/\.(ts|tsx|js|jsx|mjs|cjs)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

test("getNativeFs is null without window", () => {
  withWindow(undefined, () => {
    assert.equal(typeof globalThis.window, "undefined");
    assert.doesNotThrow(() => getNativeFs());
    assert.equal(getNativeFs(), null);
  });
});

test("getNativeFs is null in the browser", () => {
  withWindow({}, () => {
    assert.equal(getNativeFs(), null);
  });
  withWindow({ __FRAMEPILOT_DESKTOP__: true }, () => {
    assert.equal(getNativeFs(), null);
  });
  withWindow({ __FRAMEPILOT_DESKTOP__: "1" }, () => {
    assert.equal(getNativeFs(), null);
  });
});

test("apps/web source does not import Tauri plugins", () => {
  const importPattern = /(?:from|import)\s+["']@tauri-apps\/plugin-[^"']+["']|require\(["']@tauri-apps\/plugin-/;
  const offenders = listSourceFiles(webSrc).filter((filePath) => importPattern.test(fs.readFileSync(filePath, "utf8")));
  assert.deepEqual(offenders, []);
});

test("desktop capabilities grant dialog and opener without fs or shell", () => {
  const capabilities = JSON.parse(fs.readFileSync(capabilitiesPath, "utf8")) as { permissions?: unknown[] };
  const permissions = (capabilities.permissions ?? []).map((permission) =>
    typeof permission === "string" ? permission : JSON.stringify(permission),
  );
  assert.ok(
    permissions.some((permission) => permission === "dialog:default" || permission.startsWith("dialog:")),
    "expected a dialog permission",
  );
  assert.ok(
    permissions.some((permission) => permission === "opener:default" || permission.startsWith("opener:")),
    "expected an opener permission",
  );
  assert.equal(
    permissions.filter((permission) => /(^|[\s",])fs:/.test(permission) || permission.startsWith("fs:")).length,
    0,
  );
  assert.equal(
    permissions.filter((permission) => /(^|[\s",])shell:/.test(permission) || permission.startsWith("shell:")).length,
    0,
  );
});
