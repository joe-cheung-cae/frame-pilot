import type { CDPSession, Page, Response, TestInfo } from "@playwright/test";

export const CDP_METRIC_NAMES = [
  "JSHeapUsedSize",
  "JSHeapTotalSize",
  "Nodes",
  "Documents",
  "Frames",
  "LayoutCount",
  "RecalcStyleCount",
  "TaskDuration",
  "ScriptDuration",
  "LayoutDuration",
  "RecalcStyleDuration",
] as const;

export type CdpMetricName = (typeof CDP_METRIC_NAMES)[number];
export type CdpMetricSnapshot = Record<CdpMetricName, number | null>;

export type PreviewAssetTiming = {
  contentLengthBytes: number | null;
  responseDurationMs: number | null;
  responseEndMs: number | null;
  responseStartMs: number | null;
  status: number;
  urlPath: string;
};

export type BrowserSmokeMetrics = {
  cdp: CdpMetricSnapshot;
  domNodeCount: number;
  totalJSHeapSizeMB: number | null;
  usedJSHeapSizeMB: number | null;
};

type CdpMetric = {
  name: string;
  value: number;
};

type ResponseTimingSource = Pick<Response, "headers" | "request" | "status" | "url">;

function roundTwoDecimals(value: number): number {
  return Math.round(value * 100) / 100;
}

function unavailableCdpMetrics(): CdpMetricSnapshot {
  return Object.fromEntries(CDP_METRIC_NAMES.map((name) => [name, null])) as CdpMetricSnapshot;
}

export function traceEnabledFromEnv(env: NodeJS.ProcessEnv = process.env): boolean {
  return env.FRAMEPILOT_BROWSER_PERF_TRACE === "1";
}

export function metricSnapshotFromCdpMetrics(metrics: CdpMetric[]): CdpMetricSnapshot {
  const metricMap = new Map(metrics.map((metric) => [metric.name, metric.value]));
  return Object.fromEntries(CDP_METRIC_NAMES.map((name) => [name, metricMap.get(name) ?? null])) as CdpMetricSnapshot;
}

export async function collectCdpMetrics(page: Page, projectName: string): Promise<CdpMetricSnapshot> {
  if (!projectName.toLowerCase().includes("chromium")) {
    return unavailableCdpMetrics();
  }

  let session: CDPSession | null = null;
  try {
    session = await page.context().newCDPSession(page);
    await session.send("Performance.enable");
    const result = await session.send("Performance.getMetrics");
    return metricSnapshotFromCdpMetrics(result.metrics);
  } catch {
    return unavailableCdpMetrics();
  } finally {
    await session?.detach().catch(() => undefined);
  }
}

export async function collectBrowserSmokeMetrics(page: Page, projectName: string): Promise<BrowserSmokeMetrics> {
  const pageMetrics = await page.evaluate(() => {
    const performanceMemory = (
      performance as Performance & {
        memory?: { totalJSHeapSize: number; usedJSHeapSize: number };
      }
    ).memory;

    return {
      domNodeCount: document.querySelectorAll("*").length,
      totalJSHeapSizeMB: performanceMemory
        ? Math.round((performanceMemory.totalJSHeapSize / (1024 * 1024)) * 100) / 100
        : null,
      usedJSHeapSizeMB: performanceMemory
        ? Math.round((performanceMemory.usedJSHeapSize / (1024 * 1024)) * 100) / 100
        : null,
    };
  });

  return {
    ...pageMetrics,
    cdp: await collectCdpMetrics(page, projectName),
  };
}

export function previewAssetTimingFromResponse(response: ResponseTimingSource): PreviewAssetTiming {
  const headers = response.headers();
  const contentLength = Number(headers["content-length"]);
  const timing = response.request().timing();
  const responseStartMs = timing.responseStart >= 0 ? roundTwoDecimals(timing.responseStart) : null;
  const responseEndMs = timing.responseEnd >= 0 ? roundTwoDecimals(timing.responseEnd) : null;
  const responseDurationMs =
    timing.responseEnd >= 0 && timing.requestStart >= 0
      ? roundTwoDecimals(timing.responseEnd - timing.requestStart)
      : null;

  let urlPath = response.url();
  try {
    urlPath = new URL(response.url()).pathname;
  } catch {
    urlPath = response.url();
  }

  return {
    contentLengthBytes: Number.isFinite(contentLength) ? contentLength : null,
    responseDurationMs,
    responseEndMs,
    responseStartMs,
    status: response.status(),
    urlPath,
  };
}

export async function waitForFirstPreviewAssetTiming(page: Page, timeout: number): Promise<PreviewAssetTiming | null> {
  try {
    const response = await page.waitForResponse(
      (candidate) => candidate.url().includes("/api/assets/") && candidate.url().includes("/previews/"),
      { timeout },
    );
    await response.finished().catch(() => null);
    return previewAssetTimingFromResponse(response);
  } catch {
    return null;
  }
}

export async function startOptionalPerformanceTrace(page: Page): Promise<boolean> {
  if (!traceEnabledFromEnv()) {
    return false;
  }

  await page.context().tracing.start({
    screenshots: true,
    snapshots: true,
    sources: true,
  });
  return true;
}

export async function stopOptionalPerformanceTrace(page: Page, testInfo: TestInfo, traceStarted: boolean) {
  if (!traceStarted) {
    return null;
  }

  const tracePath = testInfo.outputPath("real-browser-performance-trace.zip");
  await page.context().tracing.stop({ path: tracePath });
  return tracePath;
}
