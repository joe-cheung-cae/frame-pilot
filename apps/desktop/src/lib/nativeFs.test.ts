import assert from "node:assert/strict";
import { mock, test } from "node:test";

type OpenDialogOptions = {
  directory?: boolean;
  multiple?: boolean;
  filters?: Array<{ name: string; extensions: string[] }>;
};

const openCalls: OpenDialogOptions[] = [];
const revealCalls: Array<string | string[]> = [];
const invokeCalls: Array<{ cmd: string; args?: unknown }> = [];
let openResult: unknown = null;

mock.module("@tauri-apps/plugin-dialog", {
  namedExports: {
    async open(options: OpenDialogOptions = {}) {
      openCalls.push(options);
      return openResult;
    },
  },
});

mock.module("@tauri-apps/plugin-opener", {
  namedExports: {
    async revealItemInDir(targetPath: string | string[]) {
      revealCalls.push(targetPath);
    },
  },
});

mock.module("@tauri-apps/api/core", {
  namedExports: {
    async invoke(cmd: string, args?: unknown) {
      invokeCalls.push({ cmd, args });
      return args && typeof args === "object" && "path" in args
        ? (args as { path: string }).path
        : null;
    },
  },
});

type DragDropPayload =
  | { type: "enter"; paths: string[] }
  | { type: "over" }
  | { type: "drop"; paths: string[] }
  | { type: "leave" };

const dragDropHandlers: Array<(event: { payload: DragDropPayload }) => void> = [];

mock.module("@tauri-apps/api/webview", {
  namedExports: {
    getCurrentWebview() {
      return {
        async onDragDropEvent(handler: (event: { payload: DragDropPayload }) => void) {
          dragDropHandlers.push(handler);
          return () => {
            const index = dragDropHandlers.indexOf(handler);
            if (index >= 0) {
              dragDropHandlers.splice(index, 1);
            }
          };
        },
      };
    },
  },
});

type TestWindow = {
  __TAURI__?: unknown;
  __TAURI_INTERNALS__?: unknown;
  __FRAMEPILOT_DESKTOP__?: unknown;
};

async function withWindow<T>(windowValue: TestWindow | undefined, run: () => T | Promise<T>): Promise<T> {
  const globalObject = globalThis as { window?: TestWindow };
  const hadWindow = Object.prototype.hasOwnProperty.call(globalThis, "window");
  const previous = globalObject.window;
  if (windowValue === undefined) {
    delete globalObject.window;
  } else {
    globalObject.window = windowValue;
  }
  try {
    return await run();
  } finally {
    if (hadWindow) {
      globalObject.window = previous;
    } else {
      delete globalObject.window;
    }
  }
}

function withTauriRuntime<T>(run: () => T | Promise<T>): Promise<T> {
  return withWindow({ __TAURI_INTERNALS__: {} }, run);
}

const { getNativeFs } = await import("./nativeFs.ts");

test("getNativeFs is null without window", async () => {
  await withWindow(undefined, () => {
    assert.equal(typeof globalThis.window, "undefined");
    assert.doesNotThrow(() => getNativeFs());
    assert.equal(getNativeFs(), null);
  });
});

test("getNativeFs is null in a non-Tauri browser window", async () => {
  await withWindow({}, () => {
    assert.equal(getNativeFs(), null);
  });
});

test("getNativeFs is null when the desktop flag is set without Tauri", async () => {
  await withWindow({ __FRAMEPILOT_DESKTOP__: true }, () => {
    assert.equal(getNativeFs(), null);
  });
});

test("getNativeFs returns desktop dialog wrappers in Tauri", async () => {
  await withTauriRuntime(() => {
    const nativeFs = getNativeFs();
    assert.notEqual(nativeFs, null);
    assert.equal(typeof nativeFs?.pickDirectory, "function");
    assert.equal(typeof nativeFs?.pickImageFiles, "function");
    assert.equal(typeof nativeFs?.revealInFileManager, "function");
    assert.equal(typeof nativeFs?.subscribeDragDrop, "function");
    assert.equal(typeof nativeFs?.applyDataDirectory, "function");
  });
});

test("getNativeFs returns the adapter when only window.__TAURI__ is present", async () => {
  await withWindow({ __TAURI__: {} }, () => {
    assert.notEqual(getNativeFs(), null);
  });
});

test("pickDirectory opens a single directory dialog", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    openCalls.length = 0;
    openResult = "/photos/session";
    assert.equal(await nativeFs.pickDirectory(), "/photos/session");
    assert.equal(openCalls.length, 1);
    assert.equal(openCalls[0]?.directory, true);
    assert.equal(openCalls[0]?.multiple, false);
  });
});

test("pickDirectory returns null when the dialog is cancelled", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    openResult = null;
    assert.equal(await nativeFs.pickDirectory(), null);
  });
});

test("pickImageFiles opens a JPEG PNG WebP HEIC AVIF RAW file dialog", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    openCalls.length = 0;
    openResult = ["/photos/a.jpg", "/photos/b.png"];
    assert.deepEqual(await nativeFs.pickImageFiles(), ["/photos/a.jpg", "/photos/b.png"]);
    assert.equal(openCalls.length, 1);
    assert.equal(openCalls[0]?.multiple, true);
    assert.equal(openCalls[0]?.directory, undefined);
    const extensions = openCalls[0]?.filters?.flatMap((filter) => filter.extensions) ?? [];
    assert.deepEqual(
      [...new Set(extensions)].sort(),
      ["arw", "avif", "cr3", "dng", "heic", "heif", "jpeg", "jpg", "nef", "png", "webp"],
    );
  });
});

test("pickImageFiles wraps a single selected path", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    openResult = "/photos/one.webp";
    assert.deepEqual(await nativeFs.pickImageFiles(), ["/photos/one.webp"]);
  });
});

test("pickImageFiles returns null when the dialog is cancelled", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    openResult = null;
    assert.equal(await nativeFs.pickImageFiles(), null);
  });
});

test("revealInFileManager reveals the given path", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    revealCalls.length = 0;
    await nativeFs.revealInFileManager("/projects/export.csv");
    assert.deepEqual(revealCalls, ["/projects/export.csv"]);
  });
});

test("applyDataDirectory invokes the Tauri data-dir command", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    invokeCalls.length = 0;
    await nativeFs.applyDataDirectory("/tmp/new-framepilot-data");
    assert.deepEqual(invokeCalls, [
      { cmd: "apply_data_directory", args: { path: "/tmp/new-framepilot-data" } },
    ]);
  });
});

test("subscribeDragDrop forwards Tauri drop paths", async () => {
  await withTauriRuntime(async () => {
    const nativeFs = getNativeFs();
    assert.ok(nativeFs);
    dragDropHandlers.length = 0;
    const received: unknown[] = [];
    const unlisten = await nativeFs.subscribeDragDrop((event) => {
      received.push(event);
    });
    assert.equal(dragDropHandlers.length, 1);
    dragDropHandlers[0]?.({ payload: { type: "enter", paths: ["/abs/tauri.jpg"] } });
    dragDropHandlers[0]?.({ payload: { type: "over" } });
    dragDropHandlers[0]?.({ payload: { type: "drop", paths: ["/abs/tauri.jpg"] } });
    dragDropHandlers[0]?.({ payload: { type: "leave" } });
    assert.deepEqual(received, [
      { type: "enter", paths: ["/abs/tauri.jpg"] },
      { type: "over" },
      { type: "drop", paths: ["/abs/tauri.jpg"] },
      { type: "leave" },
    ]);
    unlisten();
    assert.equal(dragDropHandlers.length, 0);
  });
});
