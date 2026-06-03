import test from "node:test";
import assert from "node:assert/strict";

import { listPageQuery } from "./api.ts";

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
