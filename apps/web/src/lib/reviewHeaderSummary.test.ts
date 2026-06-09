import test from "node:test";
import assert from "node:assert/strict";

import { reviewHeaderSummary, type ReviewHeaderPhoto } from "./reviewHeaderSummary.ts";

const photos: ReviewHeaderPhoto[] = [
  { user_status: "Pick" },
  { user_status: "Maybe" },
  { user_status: "Reject" },
  { user_status: "Unreviewed" },
];

test("formats loaded review counts for the culling header", () => {
  assert.equal(
    reviewHeaderSummary({
      activeGroupIndex: -1,
      groupCount: 0,
      photos,
      photosPartiallyLoaded: false,
      projectPhotoCount: 4,
    }),
    "3/4 loaded reviewed · 1 loaded pick",
  );
});

test("formats loaded pick counts with singular and plural labels", () => {
  assert.equal(
    reviewHeaderSummary({
      activeGroupIndex: -1,
      groupCount: 0,
      photos: [{ user_status: "Pick" }],
      photosPartiallyLoaded: false,
      projectPhotoCount: 1,
    }),
    "1/1 loaded reviewed · 1 loaded pick",
  );
  assert.equal(
    reviewHeaderSummary({
      activeGroupIndex: -1,
      groupCount: 0,
      photos: [
        { user_status: "Pick" },
        { user_status: "Pick" },
      ],
      photosPartiallyLoaded: false,
      projectPhotoCount: 2,
    }),
    "2/2 loaded reviewed · 2 loaded picks",
  );
});

test("includes partial photo loading in the culling header", () => {
  assert.equal(
    reviewHeaderSummary({
      activeGroupIndex: -1,
      groupCount: 0,
      photos,
      photosPartiallyLoaded: true,
      projectPhotoCount: 10,
    }),
    "3/4 loaded reviewed · 1 loaded pick · 4 of 10 loaded",
  );
});

test("includes active group position in the culling header", () => {
  assert.equal(
    reviewHeaderSummary({
      activeGroupIndex: 1,
      groupCount: 5,
      photos,
      photosPartiallyLoaded: false,
      projectPhotoCount: 4,
    }),
    "3/4 loaded reviewed · 1 loaded pick · Group 2 of 5",
  );
});
