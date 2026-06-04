import test from "node:test";
import assert from "node:assert/strict";

import { collectPagedList, listPageQuery } from "./api.ts";

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
