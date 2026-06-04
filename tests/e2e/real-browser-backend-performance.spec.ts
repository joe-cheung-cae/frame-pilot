import { expect, type Page, test } from "@playwright/test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readdir } from "node:fs/promises";
import path from "node:path";

const execFileAsync = promisify(execFile);
const DEFAULT_PHOTO_COUNT = 100;

function realBrowserPhotoCount() {
  const rawCount = process.env.FRAMEPILOT_BROWSER_PERF_COUNT;
  if (!rawCount) {
    return DEFAULT_PHOTO_COUNT;
  }

  const count = Number(rawCount);
  if (!Number.isInteger(count) || count <= 0) {
    throw new Error("FRAMEPILOT_BROWSER_PERF_COUNT must be a positive integer.");
  }
  return count;
}

async function generateSyntheticJpegs(outputDir: string, count: number) {
  await mkdir(outputDir, { recursive: true });
  await execFileAsync(
    path.join(process.cwd(), ".venv/bin/python"),
    [
      "-m",
      "app.devtools.synthetic_dataset",
      "--output",
      outputDir,
      "--count",
      String(count),
      "--width",
      "160",
      "--height",
      "120",
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

async function browserSmokeMetrics(page: Page) {
  return page.evaluate(() => {
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
}

function nowMs() {
  return Math.round(performance.now());
}

test("measures a real browser-backend culling workflow with generated photos", async ({ page }, testInfo) => {
  const photoCount = realBrowserPhotoCount();
  test.setTimeout(Math.max(180_000, photoCount * 1_500));

  const sourceDir = testInfo.outputPath("synthetic-source");
  const projectRoot = testInfo.outputPath("project-data");
  const imagePaths = await generateSyntheticJpegs(sourceDir, photoCount);
  expect(imagePaths).toHaveLength(photoCount);

  const timings: Record<string, number> = {};

  await page.goto("/projects/new");
  await page.getByLabel("Project name").fill(`Real Browser Backend ${Date.now()}`);
  await page.getByLabel("Project data folder").fill(projectRoot);

  let started = nowMs();
  await page.getByRole("button", { name: "Create and Import" }).click();
  await expect(page.getByRole("heading", { name: "Import Images" })).toBeVisible();
  timings.projectCreateMs = nowMs() - started;

  started = nowMs();
  await page.getByLabel("Choose image files").setInputFiles(imagePaths);
  await expect(page.getByText(`${photoCount} images imported and previewed.`)).toBeVisible({ timeout: 120_000 });
  timings.importMs = nowMs() - started;

  await page.getByRole("link", { name: "Process Project" }).click();
  started = nowMs();
  await page.getByRole("button", { name: "Run Grouping and Ranking" }).click();
  await expect(page.getByText(`${photoCount} of ${photoCount} photos · 0 failed · 100%`).first()).toBeVisible({
    timeout: 120_000,
  });
  await expect(page.getByRole("link", { name: "Open Culling Workspace" })).toBeVisible();
  timings.processMs = nowMs() - started;

  started = nowMs();
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
  const initialMetrics = await browserSmokeMetrics(page);

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
  const filterMetrics = await browserSmokeMetrics(page);

  await page.getByRole("button", { name: "All", exact: true }).click();
  const firstVisibleGroup = page.getByRole("button", { name: /^Group \d+,/ }).first();
  await expect(firstVisibleGroup).toBeVisible();
  const firstVisibleGroupLabel = await firstVisibleGroup.getAttribute("aria-label");
  const firstVisibleGroupNumber = Number(firstVisibleGroupLabel?.match(/^Group (\d+),/)?.[1]);
  expect(Number.isInteger(firstVisibleGroupNumber)).toBe(true);
  await firstVisibleGroup.click();
  started = nowMs();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByRole("button", { name: new RegExp(`^Group ${firstVisibleGroupNumber + 1},`) })).toHaveAttribute(
    "aria-current",
    "true",
  );
  timings.groupNavigationMs = nowMs() - started;
  const groupNavigationMetrics = await browserSmokeMetrics(page);

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

  console.info(
    `real-browser-backend-smoke photoCount=${photoCount} timings=${JSON.stringify(timings)} metrics=${JSON.stringify({
      initial: initialMetrics,
      afterFilter: filterMetrics,
      afterGroupNavigation: groupNavigationMetrics,
    })}`,
  );
});
