import test from "node:test";
import assert from "node:assert/strict";

import { formatCaptureTime, reviewMetadataRows } from "./reviewMetadata.ts";

test("formats capture time for the review metadata panel", () => {
  assert.equal(formatCaptureTime("2026-01-02T03:04:05"), "2026-01-02 03:04");
  assert.equal(formatCaptureTime(null), null);
});

test("builds review metadata rows from available photo fields", () => {
  assert.deepEqual(
    reviewMetadataRows({
      aperture: "2.8",
      camera_model: "FramePilotCam",
      capture_time: "2026-01-02T03:04:05",
      focal_length: "35",
      iso: 400,
      lens_model: "FramePilot 35mm",
      shutter_speed: "1/125",
    }),
    [
      ["Captured", "2026-01-02 03:04"],
      ["Camera", "FramePilotCam"],
      ["Lens", "FramePilot 35mm"],
      ["Focal length", "35 mm"],
      ["Aperture", "f/2.8"],
      ["Shutter", "1/125"],
      ["ISO", "400"],
    ],
  );
});

test("omits missing review metadata rows", () => {
  assert.deepEqual(
    reviewMetadataRows({
      aperture: null,
      camera_model: null,
      capture_time: null,
      focal_length: "",
      iso: 0,
      lens_model: null,
      shutter_speed: null,
    }),
    [],
  );
  assert.deepEqual(reviewMetadataRows(null), []);
});
