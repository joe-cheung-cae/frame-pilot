import { expect, test } from "@playwright/test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readdir } from "node:fs/promises";
import path from "node:path";

import {
  collectBrowserSmokeMetrics,
  startOptionalPerformanceTrace,
  stopOptionalPerformanceTrace,
  waitForFirstPreviewAssetTiming,
} from "./realBrowserPerformanceInstrumentation";

const execFileAsync = promisify(execFile);
const DEFAULT_PHOTO_COUNT = 100;
const DEFAULT_PHOTO_WIDTH = 160;
const DEFAULT_PHOTO_HEIGHT = 120;
const DEFAULT_JPEG_QUALITY = 88;

type RealBrowserPerfConfig = {
  count: number;
  width: number;
  height: number;
  quality: number;
};

function positiveIntegerFromEnv(name: string, fallback: number) {
  const rawValue = process.env[name];
  if (!rawValue) {
    return fallback;
  }

  const value = Number(rawValue);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`${name} must be a positive integer.`);
  }
  return value;
}

function realBrowserPerfConfig(): RealBrowserPerfConfig {
  const quality = positiveIntegerFromEnv("FRAMEPILOT_BROWSER_PERF_QUALITY", DEFAULT_JPEG_QUALITY);
  if (quality > 100) {
    throw new Error("FRAMEPILOT_BROWSER_PERF_QUALITY must be between 1 and 100.");
  }

  return {
    count: positiveIntegerFromEnv("FRAMEPILOT_BROWSER_PERF_COUNT", DEFAULT_PHOTO_COUNT),
    width: positiveIntegerFromEnv("FRAMEPILOT_BROWSER_PERF_WIDTH", DEFAULT_PHOTO_WIDTH),
    height: positiveIntegerFromEnv("FRAMEPILOT_BROWSER_PERF_HEIGHT", DEFAULT_PHOTO_HEIGHT),
    quality,
  };
}

function realBrowserOperationTimeoutMs(config: RealBrowserPerfConfig) {
  const totalMegapixels = (config.count * config.width * config.height) / 1_000_000;
  return Math.max(120_000, Math.min(900_000, Math.round(totalMegapixels * 100)));
}

async function generateSyntheticJpegs(outputDir: string, config: RealBrowserPerfConfig) {
  await mkdir(outputDir, { recursive: true });
  await execFileAsync(
    path.join(process.cwd(), ".venv/bin/python"),
    [
      "-m",
      "app.devtools.synthetic_dataset",
      "--output",
      outputDir,
      "--count",
      String(config.count),
      "--width",
      String(config.width),
      "--height",
      String(config.height),
      "--quality",
      String(config.quality),
    ],
    {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PYTHONPATH: [path.join(process.cwd(), "apps/api"), process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
      },
    },
  );

  const files = await readdir(outputDir);
  return files
    .filter((file) => file.endsWith(".jpg"))
    .sort()
    .map((file) => path.join(outputDir, file));
}

function nowMs() {
  return Math.round(performance.now());
}

test("measures a real browser-backend culling workflow with generated photos", async ({ page }, testInfo) => {
  const config = realBrowserPerfConfig();
  const photoCount = config.count;
  const operationTimeoutMs = realBrowserOperationTimeoutMs(config);
  test.setTimeout(Math.max(180_000, photoCount * 1_500));

  const sourceDir = testInfo.outputPath("synthetic-source");
  const projectRoot = testInfo.outputPath("project-data");
  const timings: Record<string, number> = {};
  const traceStarted = await startOptionalPerformanceTrace(page);
  let traceOutputPath: string | null = null;
  let traceStopped = false;

  try {
    let started = nowMs();
    const imagePaths = await generateSyntheticJpegs(sourceDir, config);
    timings.imageGenerationMs = nowMs() - started;
    expect(imagePaths).toHaveLength(photoCount);

    await page.goto("/projects/new");
    await page.getByLabel("Project name").fill(`Real Browser Backend ${Date.now()}`);
    await page.getByLabel("Project data folder").fill(projectRoot);

    started = nowMs();
    await page.getByRole("button", { name: "Create and Import" }).click();
    await expect(page.getByRole("heading", { name: "Import Images" })).toBeVisible();
    timings.projectCreateMs = nowMs() - started;

    const importResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === "POST" &&
        response.url().includes("/api/projects/") &&
        response.url().includes("/import") &&
        response.status() === 201,
    );
    started = nowMs();
    await page.getByLabel("Choose image files").setInputFiles(imagePaths);
    await expect(page.getByText(`${photoCount} images imported and previewed.`)).toBeVisible({
      timeout: operationTimeoutMs,
    });
    timings.importMs = nowMs() - started;
    const importResponse = await importResponsePromise;
    const importResponseBody = (await importResponse.json().catch(() => null)) as { timing?: unknown } | null;
    const backendImportTiming = importResponseBody?.timing ?? null;

    await page.getByRole("link", { name: "Process Project" }).click();
    started = nowMs();
    await page.getByRole("button", { name: "Run Grouping and Ranking" }).click();
    await expect(page.getByText(`${photoCount} of ${photoCount} photos · 0 failed · 100%`).first()).toBeVisible({
      timeout: operationTimeoutMs,
    });
    await expect(page.getByRole("link", { name: "Open Culling Workspace" })).toBeVisible();
    timings.processMs = nowMs() - started;

    started = nowMs();
    const previewAssetTimingPromise = waitForFirstPreviewAssetTiming(page, 60_000);
    await page.getByRole("link", { name: "Open Culling Workspace" }).click();
    await expect(page.getByRole("heading", { name: /^frame_\d+\.jpg$/ })).toBeVisible({ timeout: 60_000 });
    const preview = page.locator('img[src*="/api/assets/"][src*="/previews/"]').first();
    await expect(preview).toBeVisible({ timeout: 60_000 });
    await expect
      .poll(() =>
        preview.evaluate((image) => {
          const element = image as HTMLImageElement;
          return element.complete && element.naturalWidth > 0;
        }),
      )
      .toBe(true);
    timings.firstPreviewMs = nowMs() - started;
    const previewAssetTiming = await previewAssetTimingPromise;
    const initialMetrics = await collectBrowserSmokeMetrics(page, testInfo.project.name);

    const statusResponse = page.waitForResponse(
      (response) =>
        response.request().method() === "PATCH" &&
        response.url().includes("/api/projects/") &&
        response.url().includes("/photos/") &&
        response.status() === 200,
    );
    started = nowMs();
    await page.getByRole("button", { name: "Set active photo to Pick" }).click();
    await statusResponse;
    timings.statusUpdateMs = nowMs() - started;

    started = nowMs();
    await page.getByRole("button", { name: "Picks" }).click();
    await expect(page.getByRole("button", { name: "Picks" })).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByText(`1/${photoCount} loaded reviewed`)).toBeVisible();
    timings.filterSwitchMs = nowMs() - started;
    const filterMetrics = await collectBrowserSmokeMetrics(page, testInfo.project.name);

    await page.getByRole("button", { name: "All", exact: true }).click();
    const firstVisibleGroup = page.getByRole("button", { name: /^Group \d+,/ }).first();
    await expect(firstVisibleGroup).toBeVisible();
    const firstVisibleGroupLabel = await firstVisibleGroup.getAttribute("aria-label");
    const firstVisibleGroupNumber = Number(firstVisibleGroupLabel?.match(/^Group (\d+),/)?.[1]);
    expect(Number.isInteger(firstVisibleGroupNumber)).toBe(true);
    await firstVisibleGroup.click();
    started = nowMs();
    await page.keyboard.press("ArrowDown");
    await expect(
      page.getByRole("button", { name: new RegExp(`^Group ${firstVisibleGroupNumber + 1},`) }),
    ).toHaveAttribute("aria-current", "true");
    timings.groupNavigationMs = nowMs() - started;
    const groupNavigationMetrics = await collectBrowserSmokeMetrics(page, testInfo.project.name);

    await page.getByRole("link", { name: "Export" }).click();
    await expect(page.getByRole("heading", { name: "Export Selection" })).toBeVisible();
    const maybeCheckbox = page.getByLabel("Maybe");
    if (await maybeCheckbox.isChecked()) {
      await maybeCheckbox.uncheck();
    }

    started = nowMs();
    await page.getByRole("button", { name: "Export" }).click();
    await expect(page.getByText("1 photo exported.")).toBeVisible({ timeout: 60_000 });
    await expect(page.getByRole("link", { name: "Download CSV" })).toBeVisible();
    timings.exportMs = nowMs() - started;

    traceOutputPath = await stopOptionalPerformanceTrace(page, testInfo, traceStarted);
    traceStopped = true;

    console.info(
      `real-browser-backend-smoke config=${JSON.stringify(config)} timings=${JSON.stringify(
        timings,
      )} metrics=${JSON.stringify({
        initial: initialMetrics,
        afterFilter: filterMetrics,
        afterGroupNavigation: groupNavigationMetrics,
      })} importTiming=${JSON.stringify(backendImportTiming)} previewAssetTiming=${JSON.stringify(
        previewAssetTiming,
      )} trace=${JSON.stringify({
        enabled: traceStarted,
        outputPath: traceOutputPath,
      })}`,
    );
  } finally {
    if (traceStarted && !traceStopped) {
      await stopOptionalPerformanceTrace(page, testInfo, true).catch(() => null);
    }
  }
});
