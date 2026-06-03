import { expect, test } from "@playwright/test";
import { Buffer } from "node:buffer";

function pngFixture(color: "green" | "blue"): Buffer {
  const fixtures = {
    green:
      "iVBORw0KGgoAAAANSUhEUgAAAGAAAABICAIAAACGBWc0AAABRElEQVR4nO2b7QkCMRBEx5R5JaSClGAFKcH6rgQRw004QUVFB3zv5/5alvt4zCaH1pe29OOp6oZGXTqs63odx25GbenUJZVtLttEdnNp/10vgT0dk+olsCcl1UtgT1H1EthTVL0E9qSkegnsqSXV8aAH3ocHDfAggwcZPMjgQQYPCvr340HCg+o7ORceNMCDDB5k8CCDBxk8yOBBQbMgD7qABw3Yixn2Yoa9WNw3m73YBfZiIg8yeFD95jkm8qABeZAhDzLkQQYPMuRBQT7NXkzkQXV+NPCgAXmQIQ8y5EFB/y/yIHFO2uBBhjyoTtMgD/r1N5v7Yg9mxH2xPo2I+2ITeJDhvpghDzKcD6rf9B32YgM86MPvIB7U78+Ie/MiDxIeZPAggwfVaRp4UFhWv0EeZPCgV54jPEh4kPAgvfDuPFk/A1l3Ly05RUKtAAAAAElFTkSuQmCC",
    blue: "iVBORw0KGgoAAAANSUhEUgAAAGAAAABICAIAAACGBWc0AAABSUlEQVR4nO2bywkCQRBEy4lrIzEEDwZhCB4mEkOYgDYEEYetYQUVFS3wvWOfmmY/j+qZzfZwqvtpd2y6oVKXNvM8X8exmlHdT9QllWUuy0RWc6n/XS+BPe2S6iWwJyXVS2BPUfUS2FNUvQT2pKR6CeypJtXxoAfehwd18CCDBxk8yOBBBg8K+vfjQcKD2js5Fx7UwYMMHmTwIIMHGTzI4EFBsyAPuoAHddiLGfZihr1Y3DebvdgF9mIiDzJ4UPvmOSbyoA55kCEPMuRBBg8y5EFBPs1eTORBbXw08KAOeZAhDzLkQUH/L/IgcU7a4EGGPKgN0yAP+vU3m/tiD2bEfbFpGBH3xQbwIMN9MUMeZDgf1L7pO+zFOnjQh99BPGi6PyPuzYs8SHiQwYMMHtSGaeBBYVn9AnmQwYNeeY7wIOFBwoP0wrvzZP0MbuQwvXfq6ToAAAAASUVORK5CYII=",
  };
  return Buffer.from(fixtures[color], "base64");
}

test("runs a real local import, process, pick, and CSV export smoke flow", async ({ page }) => {
  await page.goto("/projects/new");
  await page.getByLabel("Project name").fill(`Real Smoke ${Date.now()}`);
  await page.getByRole("button", { name: "Create and Import" }).click();
  await expect(page.getByRole("heading", { name: "Import Images" })).toBeVisible();

  await page.getByLabel("Choose image files").setInputFiles([
    {
      name: "real-smoke-1.png",
      mimeType: "image/png",
      buffer: pngFixture("green"),
    },
    {
      name: "real-smoke-2.png",
      mimeType: "image/png",
      buffer: pngFixture("blue"),
    },
  ]);

  await expect(page.getByText("2 images imported and previewed.")).toBeVisible();
  await page.getByRole("link", { name: "Process Project" }).click();
  await page.getByRole("button", { name: "Run Grouping and Ranking" }).click();
  await expect(page.getByRole("link", { name: "Open Culling Workspace" })).toBeVisible();

  await page.getByRole("link", { name: "Open Culling Workspace" }).click();
  await expect(page.getByRole("heading", { name: /real-smoke-/ })).toBeVisible();
  await page.getByRole("button", { name: "Set active photo to Pick" }).click();

  await page.getByRole("link", { name: "Export" }).click();
  await expect(page.getByRole("heading", { name: "Export Selection" })).toBeVisible();
  await page.getByRole("checkbox", { name: "Maybe" }).uncheck();
  await page.getByRole("button", { name: "Export" }).click();

  const downloadLink = page.getByRole("link", { name: "Download CSV" });
  await expect(downloadLink).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await downloadLink.click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  expect(stream).not.toBeNull();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const csv = Buffer.concat(chunks).toString("utf8");

  expect(csv).toContain("filename,original_path,capture_time,camera_model,lens_model");
  expect(csv).toContain("Pick");
  expect(csv).toContain("real-smoke-");
});
