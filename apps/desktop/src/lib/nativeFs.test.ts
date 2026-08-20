import assert from "node:assert/strict";
import { mock, test } from "node:test";

type OpenDialogOptions = {
  directory?: boolean;
  multiple?: boolean;
  filters?: Array<{ name: string; extensions: string[] }>;
};

const openCalls: OpenDialogOptions[] = [];
const revealCalls: Array<string | string[]> = [];
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

const { getNativeFs } = await import("./nativeFs.ts");

test("getNativeFs returns desktop dialog wrappers", () => {
  const nativeFs = getNativeFs();
  assert.notEqual(nativeFs, null);
  assert.equal(typeof nativeFs?.pickDirectory, "function");
  assert.equal(typeof nativeFs?.pickImageFiles, "function");
  assert.equal(typeof nativeFs?.revealInFileManager, "function");
  assert.equal(typeof nativeFs?.subscribeDragDrop, "function");
});

test("pickDirectory opens a single directory dialog", async () => {
  const nativeFs = getNativeFs();
  assert.ok(nativeFs);
  openCalls.length = 0;
  openResult = "/photos/session";
  assert.equal(await nativeFs.pickDirectory(), "/photos/session");
  assert.equal(openCalls.length, 1);
  assert.equal(openCalls[0]?.directory, true);
  assert.equal(openCalls[0]?.multiple, false);
});

test("pickDirectory returns null when the dialog is cancelled", async () => {
  const nativeFs = getNativeFs();
  assert.ok(nativeFs);
  openResult = null;
  assert.equal(await nativeFs.pickDirectory(), null);
});

test("pickImageFiles opens a JPEG PNG WebP file dialog", async () => {
  const nativeFs = getNativeFs();
  assert.ok(nativeFs);
  openCalls.length = 0;
  openResult = ["/photos/a.jpg", "/photos/b.png"];
  assert.deepEqual(await nativeFs.pickImageFiles(), ["/photos/a.jpg", "/photos/b.png"]);
  assert.equal(openCalls.length, 1);
  assert.equal(openCalls[0]?.multiple, true);
  assert.equal(openCalls[0]?.directory, undefined);
  const extensions = openCalls[0]?.filters?.flatMap((filter) => filter.extensions) ?? [];
  assert.deepEqual([...new Set(extensions)].sort(), ["jpeg", "jpg", "png", "webp"]);
});

test("pickImageFiles wraps a single selected path", async () => {
  const nativeFs = getNativeFs();
  assert.ok(nativeFs);
  openResult = "/photos/one.webp";
  assert.deepEqual(await nativeFs.pickImageFiles(), ["/photos/one.webp"]);
});

test("pickImageFiles returns null when the dialog is cancelled", async () => {
  const nativeFs = getNativeFs();
  assert.ok(nativeFs);
  openResult = null;
  assert.equal(await nativeFs.pickImageFiles(), null);
});

test("revealInFileManager reveals the given path", async () => {
  const nativeFs = getNativeFs();
  assert.ok(nativeFs);
  revealCalls.length = 0;
  await nativeFs.revealInFileManager("/projects/export.csv");
  assert.deepEqual(revealCalls, ["/projects/export.csv"]);
});

test("subscribeDragDrop forwards Tauri drop paths", async () => {
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
