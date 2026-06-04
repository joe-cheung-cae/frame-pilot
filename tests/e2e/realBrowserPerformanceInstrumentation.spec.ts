import { expect, test } from "@playwright/test";

import {
  CDP_METRIC_NAMES,
  metricSnapshotFromCdpMetrics,
  previewAssetTimingFromResponse,
  traceEnabledFromEnv,
} from "./realBrowserPerformanceInstrumentation";

test("normalizes requested CDP metrics and marks missing values unavailable", () => {
  const snapshot = metricSnapshotFromCdpMetrics([
    { name: "JSHeapUsedSize", value: 1234 },
    { name: "Nodes", value: 42 },
    { name: "TaskDuration", value: 1.25 },
    { name: "UnexpectedMetric", value: 999 },
  ]);

  expect(snapshot.JSHeapUsedSize).toBe(1234);
  expect(snapshot.Nodes).toBe(42);
  expect(snapshot.TaskDuration).toBe(1.25);
  expect(snapshot.JSHeapTotalSize).toBeNull();
  expect(Object.keys(snapshot).sort()).toEqual([...CDP_METRIC_NAMES].sort());
});

test("extracts preview asset status, content length, and approximate request timing", () => {
  const timing = previewAssetTimingFromResponse({
    status: () => 200,
    url: () => "http://127.0.0.1:8000/api/assets/project-1/previews/frame_0001.webp",
    headers: () => ({ "content-length": "4567" }),
    request: () => ({
      timing: () => ({
        startTime: 1_776_000_000_000,
        domainLookupStart: -1,
        domainLookupEnd: -1,
        connectStart: -1,
        secureConnectionStart: -1,
        connectEnd: -1,
        requestStart: 3.25,
        responseStart: 8.5,
        responseEnd: 14.75,
      }),
    }),
  });

  expect(timing).toEqual({
    contentLengthBytes: 4567,
    responseDurationMs: 11.5,
    responseEndMs: 14.75,
    responseStartMs: 8.5,
    status: 200,
    urlPath: "/api/assets/project-1/previews/frame_0001.webp",
  });
});

test("keeps preview asset timing optional when browser timing or content length is unavailable", () => {
  const timing = previewAssetTimingFromResponse({
    status: () => 200,
    url: () => "not a valid url",
    headers: () => ({}),
    request: () => ({
      timing: () => ({
        startTime: -1,
        domainLookupStart: -1,
        domainLookupEnd: -1,
        connectStart: -1,
        secureConnectionStart: -1,
        connectEnd: -1,
        requestStart: -1,
        responseStart: -1,
        responseEnd: -1,
      }),
    }),
  });

  expect(timing).toEqual({
    contentLengthBytes: null,
    responseDurationMs: null,
    responseEndMs: null,
    responseStartMs: null,
    status: 200,
    urlPath: "not a valid url",
  });
});

test("enables manual performance trace capture only for explicit opt-in", () => {
  expect(traceEnabledFromEnv({ FRAMEPILOT_BROWSER_PERF_TRACE: "1" })).toBe(true);
  expect(traceEnabledFromEnv({ FRAMEPILOT_BROWSER_PERF_TRACE: "true" })).toBe(false);
  expect(traceEnabledFromEnv({})).toBe(false);
});
