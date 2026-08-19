import test from "node:test";
import assert from "node:assert/strict";

import {
  API_BASE,
  assetUrl,
  chunkItems,
  collectPagedList,
  exportDownloadUrl,
  IMPORT_UPLOAD_BATCH_SIZE,
  listPageQuery,
} from "./api.ts";

type TestWindow = {
  __FRAMEPILOT_API_BASE__?: string;
};

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

test("builds empty list query when pagination is omitted", () => {
  assert.equal(listPageQuery(), "");
  assert.equal(listPageQuery({}), "");
});

test("builds list pagination query parameters", () => {
  assert.equal(listPageQuery({ limit: 50 }), "?limit=50");
  assert.equal(listPageQuery({ offset: 100 }), "?offset=100");
  assert.equal(listPageQuery({ limit: 50, offset: 100 }), "?limit=50&offset=100");
});

test("keeps explicit zero offset for first paged result", () => {
  assert.equal(listPageQuery({ limit: 25, offset: 0 }), "?limit=25&offset=0");
});

test("collects every page until the final page is under the page limit", async () => {
  const calls: { limit: number; offset: number }[] = [];
  const pages = new Map([
    [0, ["first", "second"]],
    [2, ["third", "fourth"]],
    [4, ["fifth"]],
  ]);

  const items = await collectPagedList(async (options) => {
    calls.push(options);
    return pages.get(options.offset) ?? [];
  }, 2);

  assert.deepEqual(items, ["first", "second", "third", "fourth", "fifth"]);
  assert.deepEqual(calls, [
    { limit: 2, offset: 0 },
    { limit: 2, offset: 2 },
    { limit: 2, offset: 4 },
  ]);
});

test("fetches one empty page after exact page-size boundaries", async () => {
  const offsets: number[] = [];
  const items = await collectPagedList(async (options) => {
    offsets.push(options.offset);
    return options.offset === 0 ? [1, 2] : [];
  }, 2);

  assert.deepEqual(items, [1, 2]);
  assert.deepEqual(offsets, [0, 2]);
});

test("rejects invalid page limits", async () => {
  await assert.rejects(() => collectPagedList(async () => [], 0), /positive integer/);
  await assert.rejects(() => collectPagedList(async () => [], 1.5), /positive integer/);
});

test("chunks files into bounded import upload batches", () => {
  const files = Array.from({ length: 250 }, (_, index) => `file-${index}`);
  const batches = chunkItems(files, IMPORT_UPLOAD_BATCH_SIZE);
  assert.equal(batches.length, 3);
  assert.equal(batches[0].length, 100);
  assert.equal(batches[1].length, 100);
  assert.equal(batches[2].length, 50);
  assert.deepEqual(batches.flat(), files);
});

test("rejects invalid import batch sizes", () => {
  assert.throws(() => chunkItems(["a"], 0), /positive integer/);
});

test("assetUrl encodes special characters and supports windows separators", () => {
  const posix = assetUrl("proj", "/data/projects/proj/thumbnails/holiday #1 (50%).jpg");
  assert.equal(
    posix,
    `${API_BASE}/api/assets/proj/${encodeURIComponent("thumbnails")}/${encodeURIComponent("holiday #1 (50%).jpg")}`,
  );
  assert.equal(posix?.includes("#"), false);
  assert.equal(posix?.includes(" "), false);

  const windows = assetUrl("proj", "C:\\data\\projects\\proj\\previews\\shot.jpg");
  assert.equal(
    windows,
    `${API_BASE}/api/assets/proj/${encodeURIComponent("previews")}/${encodeURIComponent("shot.jpg")}`,
  );
});

test("assetUrl and exportDownloadUrl use the injected host at call time", () => {
  const injected = "http://127.0.0.1:18000";
  withWindow({ __FRAMEPILOT_API_BASE__: injected }, () => {
    const posix = assetUrl("proj", "/data/projects/proj/thumbnails/holiday #1 (50%).jpg");
    assert.equal(
      posix,
      `${injected}/api/assets/proj/${encodeURIComponent("thumbnails")}/${encodeURIComponent("holiday #1 (50%).jpg")}`,
    );
    assert.equal(posix?.includes("#"), false);
    assert.equal(posix?.includes(" "), false);
    assert.equal(exportDownloadUrl("proj", "exp-1"), `${injected}/api/projects/proj/exports/exp-1/download`);
  });
});

test("assetUrl and exportDownloadUrl reread the API base on each call", () => {
  const first = "http://127.0.0.1:18000";
  const second = "http://127.0.0.1:18001";
  withWindow({ __FRAMEPILOT_API_BASE__: first }, () => {
    assert.equal(exportDownloadUrl("proj", "exp-1"), `${first}/api/projects/proj/exports/exp-1/download`);
    assert.equal(
      assetUrl("proj", "C:\\data\\projects\\proj\\previews\\shot.jpg"),
      `${first}/api/assets/proj/${encodeURIComponent("previews")}/${encodeURIComponent("shot.jpg")}`,
    );
  });
  withWindow({ __FRAMEPILOT_API_BASE__: second }, () => {
    assert.equal(exportDownloadUrl("proj", "exp-1"), `${second}/api/projects/proj/exports/exp-1/download`);
    assert.equal(
      assetUrl("proj", "C:\\data\\projects\\proj\\previews\\shot.jpg"),
      `${second}/api/assets/proj/${encodeURIComponent("previews")}/${encodeURIComponent("shot.jpg")}`,
    );
  });
});
