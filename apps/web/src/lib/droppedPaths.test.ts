import test from "node:test";
import assert from "node:assert/strict";

import { collectDroppedPaths, importDropOverlayPointerEvents } from "./droppedPaths.ts";

function dropEvent(dataTransfer: {
  files?: ArrayLike<{ path?: string | null; name?: string }> | null;
  items?: ArrayLike<{
    kind?: string;
    getAsFile?: () => { path?: string | null } | null;
  }> | null;
  types?: ArrayLike<string> | null;
  getData?: (format: string) => string;
} | null) {
  return { dataTransfer };
}

test("collectDroppedPaths reads File.path values from a drop event", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [
          { path: "/abs/a.jpg", name: "a.jpg" },
          { path: "/abs/b.png", name: "b.png" },
        ],
        types: ["Files"],
      }),
    ),
    ["/abs/a.jpg", "/abs/b.png"],
  );
});

test("collectDroppedPaths ignores files that have no filesystem path", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [{ name: "a.jpg" }, { path: "", name: "b.png" }, { path: "   ", name: "c.webp" }],
        types: ["Files"],
      }),
    ),
    [],
  );
});

test("collectDroppedPaths reads file:// URIs from text/uri-list", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [],
        types: ["text/uri-list"],
        getData: (format) =>
          format === "text/uri-list"
            ? "file:///photos/a.jpg\n#comment\nfile:///photos/my%20album/b.png\nhttps://example.com/c.jpg\n"
            : "",
      }),
    ),
    ["/photos/a.jpg", "/photos/my album/b.png"],
  );
});

test("collectDroppedPaths decodes Windows file:// URIs", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [],
        types: ["text/uri-list"],
        getData: (format) => (format === "text/uri-list" ? "file:///C:/Users/joe/Pictures/a.jpg" : ""),
      }),
    ),
    ["C:/Users/joe/Pictures/a.jpg"],
  );
});

test("collectDroppedPaths keeps Windows File.path strings", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [{ path: "D:\\card\\burst\\DSC_0001.JPG", name: "DSC_0001.JPG" }],
        types: ["Files"],
      }),
    ),
    ["D:\\card\\burst\\DSC_0001.JPG"],
  );
});

test("collectDroppedPaths reads File.path from dataTransfer items", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [],
        items: [
          {
            kind: "file",
            getAsFile: () => ({ path: "/abs/from-item.webp" }),
          },
        ],
        types: ["Files"],
      }),
    ),
    ["/abs/from-item.webp"],
  );
});

test("collectDroppedPaths reads absolute paths from text/plain", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [],
        types: ["text/plain"],
        getData: (format) => (format === "text/plain" ? "/abs/folder\n/abs/one.jpg\nrelative.jpg\n" : ""),
      }),
    ),
    ["/abs/folder", "/abs/one.jpg"],
  );
});

test("collectDroppedPaths returns an empty list without dataTransfer", () => {
  assert.deepEqual(collectDroppedPaths(undefined), []);
  assert.deepEqual(collectDroppedPaths(null), []);
  assert.deepEqual(collectDroppedPaths({}), []);
  assert.deepEqual(collectDroppedPaths(dropEvent(null)), []);
});

test("collectDroppedPaths deduplicates paths from files and uri-list", () => {
  assert.deepEqual(
    collectDroppedPaths(
      dropEvent({
        files: [{ path: "/abs/a.jpg", name: "a.jpg" }, { path: "/abs/a.jpg", name: "a.jpg" }],
        types: ["Files", "text/uri-list"],
        getData: (format) => (format === "text/uri-list" ? "file:///abs/a.jpg\nfile:///abs/b.png" : ""),
      }),
    ),
    ["/abs/a.jpg", "/abs/b.png"],
  );
});

test("importDropOverlayPointerEvents is none unless a drag is active", () => {
  assert.equal(importDropOverlayPointerEvents(false), "none");
  assert.equal(importDropOverlayPointerEvents(true), "auto");
});
