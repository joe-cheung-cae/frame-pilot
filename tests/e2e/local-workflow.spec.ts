import { expect, test } from "@playwright/test";

const project = {
  id: "project-1",
  name: "E2E Shoot",
  root_path: "/tmp/framepilot/e2e",
  total_images: 3,
  processed_images: 0,
  created_at: "2026-06-02T00:00:00Z",
  updated_at: "2026-06-02T00:00:00Z",
};

const emptyProject = {
  ...project,
  id: "empty-project",
  name: "Empty Shoot",
  total_images: 0,
  processed_images: 0,
};

const completedJob = {
  id: "job-1",
  project_id: project.id,
  job_type: "processing",
  status: "complete",
  current_step: "complete",
  total_items: project.total_images,
  processed_items: project.total_images,
  failed_items: 0,
  progress_percent: 100,
  error_message: null,
  started_at: "2026-06-02T00:00:00Z",
  completed_at: "2026-06-02T00:00:01Z",
};

const photos = [
  {
    id: "photo-1",
    project_id: project.id,
    filename: "frame-001.jpg",
    file_size: 1234,
    width: 80,
    height: 60,
    thumbnail_path: "thumbnails/frame-001.webp",
    preview_path: "previews/frame-001.webp",
    sharpness_score: 0.82,
    blur_score: 0.18,
    exposure_score: 0.73,
    contrast_score: 0.64,
    noise_score: 0.2,
    face_presence: true,
    face_sharpness_score: 0.6,
    eye_open_confidence: 0.8,
    face_quality_score: 0.7,
    aesthetic_score: 0.68,
    overall_score: 0.78,
    ai_recommendation: "Pick",
    recommendation_explanation: "Recommended because it has the highest overall score in this group.",
    user_status: "Unreviewed",
    star_rating: 0,
    group_id: "group-1",
  },
  {
    id: "photo-2",
    project_id: project.id,
    filename: "frame-002.jpg",
    file_size: 1235,
    width: 80,
    height: 60,
    thumbnail_path: "thumbnails/frame-002.webp",
    preview_path: "previews/frame-002.webp",
    sharpness_score: 0.52,
    blur_score: 0.48,
    exposure_score: 0.62,
    contrast_score: 0.5,
    noise_score: 0.22,
    face_presence: false,
    face_sharpness_score: 0,
    eye_open_confidence: null,
    face_quality_score: 0,
    aesthetic_score: 0.56,
    overall_score: 0.55,
    ai_recommendation: "Maybe",
    recommendation_explanation: "Marked as Maybe because it is close to the strongest image.",
    user_status: "Unreviewed",
    star_rating: 0,
    group_id: "group-1",
  },
  {
    id: "photo-3",
    project_id: project.id,
    filename: "frame-003.jpg",
    file_size: 1236,
    width: 80,
    height: 60,
    thumbnail_path: "thumbnails/frame-003.webp",
    preview_path: "previews/frame-003.webp",
    sharpness_score: 0.62,
    blur_score: 0.38,
    exposure_score: 0.67,
    contrast_score: 0.58,
    noise_score: 0.25,
    face_presence: false,
    face_sharpness_score: 0,
    eye_open_confidence: null,
    face_quality_score: 0,
    aesthetic_score: 0.6,
    overall_score: 0.61,
    ai_recommendation: "Pick",
    recommendation_explanation: "Recommended because it has the strongest available quality signals.",
    user_status: "Unreviewed",
    star_rating: 0,
    group_id: "group-2",
  },
] as const;

const groups = [
  {
    id: "group-1",
    project_id: project.id,
    group_type: "duplicate",
    representative_photo_id: "photo-1",
    photo_count: 2,
    score_summary: JSON.stringify({
      best_score: 0.78,
      confidence: "high",
      explanation: "High confidence because the top photo leads the next candidate by 0.23.",
      recommendation_counts: { Maybe: 1, Pick: 1, Reject: 0, Unreviewed: 0 },
      score_gap: 0.23,
      top_photo_id: "photo-1",
    }),
  },
  {
    id: "group-2",
    project_id: project.id,
    group_type: "single",
    representative_photo_id: "photo-3",
    photo_count: 1,
    score_summary: JSON.stringify({
      best_score: 0.61,
      confidence: "low",
      explanation: "Low confidence because this group has no similar alternative to compare.",
      recommendation_counts: { Maybe: 0, Pick: 1, Reject: 0, Unreviewed: 0 },
      score_gap: 0,
      top_photo_id: "photo-3",
    }),
  },
];

let photoPatches: { patch: { star_rating?: number; user_status?: string }; photoId: string | undefined }[] = [];
let batchPhotoPatches: { patch: { star_rating?: number; user_status?: string }; photoIds: string[] }[] = [];
let photoListRequests = 0;

test.beforeEach(async ({ page }) => {
  photoPatches = [];
  batchPhotoPatches = [];
  photoListRequests = 0;
  let currentProject = { ...project };
  let currentPhotos = photos.map((photo) => ({ ...photo }));
  let currentJob: typeof completedJob | null = null;

  await page.route("**/api/projects", async (route) => {
    if (route.request().method() === "POST") {
      currentProject = { ...currentProject, total_images: 0, processed_images: 0 };
      await route.fulfill({ json: currentProject, status: 201 });
      return;
    }
    await route.fulfill({ json: [currentProject, emptyProject] });
  });

  await page.route(`**/api/projects/${project.id}`, async (route) => {
    await route.fulfill({ json: currentProject });
  });

  await page.route(`**/api/projects/${project.id}/process`, async (route) => {
    if (currentProject.total_images === 0) {
      await route.fulfill({ json: { detail: "Import photos before processing this project" }, status: 422 });
      return;
    }
    currentProject = { ...currentProject, processed_images: currentProject.total_images };
    currentJob = {
      ...completedJob,
      total_items: currentProject.total_images,
      processed_items: currentProject.total_images,
    };
    await route.fulfill({
      json: currentJob,
      status: 202,
    });
  });

  await page.route(`**/api/projects/${project.id}/jobs`, async (route) => {
    await route.fulfill({ json: currentJob ? [currentJob] : [] });
  });

  await page.route(`**/api/projects/${project.id}/jobs/*`, async (route) => {
    const jobId = route.request().url().split("/").at(-1);
    if (currentJob?.id !== jobId) {
      await route.fulfill({ json: { detail: "Processing job not found" }, status: 404 });
      return;
    }
    await route.fulfill({ json: currentJob });
  });

  await page.route(`**/api/projects/${project.id}/import`, async (route) => {
    currentProject = { ...currentProject, total_images: currentProject.total_images + 1, processed_images: 0 };
    const imported = {
      ...photos[0],
      id: "imported-photo",
      filename: "uploaded-frame.jpg",
      thumbnail_path: "thumbnails/uploaded-frame.webp",
      preview_path: "previews/uploaded-frame.webp",
    };
    currentPhotos = [imported, ...currentPhotos];
    await route.fulfill({ json: { imported: [imported], skipped: [] }, status: 201 });
  });

  await page.route(`**/api/projects/${project.id}/photos`, async (route) => {
    photoListRequests += 1;
    await route.fulfill({ json: currentPhotos });
  });

  await page.route(`**/api/projects/${project.id}/photos/*`, async (route) => {
    if (route.request().url().endsWith("/photos/batch")) {
      await route.fallback();
      return;
    }
    const photoId = route.request().url().split("/").at(-1);
    const patch = route.request().postDataJSON() as { user_status?: string; star_rating?: number };
    photoPatches.push({ patch, photoId });
    currentPhotos = currentPhotos.map((photo) => (photo.id === photoId ? { ...photo, ...patch } : photo));
    await route.fulfill({ json: currentPhotos.find((photo) => photo.id === photoId) });
  });

  await page.route(`**/api/projects/${project.id}/photos/batch`, async (route) => {
    const payload = route.request().postDataJSON() as {
      photo_ids: string[];
      star_rating?: number;
      user_status?: string;
    };
    const { photo_ids, ...patch } = payload;
    batchPhotoPatches.push({ patch, photoIds: photo_ids });
    currentPhotos = currentPhotos.map((photo) => (photo_ids.includes(photo.id) ? { ...photo, ...patch } : photo));
    await route.fulfill({ json: currentPhotos.filter((photo) => photo_ids.includes(photo.id)) });
  });

  await page.route(`**/api/projects/${project.id}/groups`, async (route) => {
    await route.fulfill({ json: groups });
  });

  await page.route(`**/api/projects/${project.id}/export`, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ json: [] });
      return;
    }

    await route.fulfill({
      json: {
        id: "export-1",
        project_id: project.id,
        mode: "csv",
        status: "complete",
        selected_count: currentPhotos.filter((photo) => photo.user_status === "Pick").length,
        statuses: '["Pick"]',
        output_path: "/tmp/framepilot/e2e/exports/selection-export-1.csv",
        created_at: "2026-06-02T00:00:00Z",
      },
      status: 201,
    });
  });

  await page.route("**/api/assets/**", async (route) => {
    await route.fulfill({
      body: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lK3wLwAAAABJRU5ErkJggg==",
        "base64",
      ),
      contentType: "image/png",
    });
  });
});

test("walks the local project review and export flow in a browser", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Recent Projects" })).toBeVisible();
  await page.getByRole("link", { name: /E2E Shoot/ }).click();
  await expect(page).toHaveURL(/\/projects\/project-1\/process$/);

  await page.goto(`/projects/${project.id}/process`);
  await page.getByRole("button", { name: "Run Grouping and Ranking" }).click();
  await expect(page.getByText("3 of 3 photos · 0 failed · 100%")).toBeVisible();
  await expect(page.locator("p").filter({ hasText: /^complete$/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open Culling Workspace" })).toBeVisible();

  await page.getByRole("link", { name: "Open Culling Workspace" }).click();
  await expect(page.getByRole("heading", { name: "E2E Shoot" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Toggle zoom" })).toHaveAttribute("aria-pressed", "false");
  await page.keyboard.press("z");
  await expect(page.getByRole("button", { name: "Toggle zoom" })).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("z");
  await expect(page.getByRole("button", { name: "Toggle zoom" })).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("button", { name: "Toggle compare" })).toHaveAttribute("aria-pressed", "false");
  await page.keyboard.press("c");
  await expect(page.getByRole("button", { name: "Toggle compare" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("img", { name: "Compare frame-001.jpg" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Compare frame-002.jpg" })).toBeVisible();
  await page.keyboard.press("c");
  await expect(page.getByRole("button", { name: "Toggle compare" })).toHaveAttribute("aria-pressed", "false");
  await page.keyboard.press("f");
  await expect(page.getByRole("button", { name: "All" })).toBeFocused();
  await expect(page.getByText("High confidence").first()).toBeVisible();
  await expect(page.getByText("High confidence because the top photo leads the next candidate by 0.23.")).toBeVisible();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByRole("heading", { name: "frame-003.jpg" })).toBeVisible();
  await expect(page.getByText("Low confidence because this group has no similar alternative to compare.")).toBeVisible();
  await page.keyboard.press("ArrowUp");
  await expect(page.getByRole("heading", { name: "frame-001.jpg" })).toBeVisible();
  const initialPatchCount = photoPatches.length;
  const initialPhotoListRequests = photoListRequests;
  await page.keyboard.press("5");
  await expect.poll(() => photoPatches.length).toBe(initialPatchCount + 1);
  expect(photoPatches.at(-1)).toEqual({ patch: { star_rating: 5 }, photoId: "photo-1" });
  await page.getByRole("button", { name: "Clear rating" }).click();
  await expect.poll(() => photoPatches.length).toBe(initialPatchCount + 2);
  expect(photoPatches.at(-1)).toEqual({ patch: { star_rating: 0 }, photoId: "photo-1" });
  await page.keyboard.press("0");
  await expect.poll(() => photoPatches.length).toBe(initialPatchCount + 3);
  expect(photoPatches.at(-1)).toEqual({ patch: { star_rating: 0 }, photoId: "photo-1" });
  const initialBatchPatchCount = batchPhotoPatches.length;
  await page.getByRole("button", { name: "Set visible photos to rejected", exact: true }).click();
  await expect.poll(() => batchPhotoPatches.length).toBe(initialBatchPatchCount + 1);
  expect(batchPhotoPatches.at(-1)).toEqual({
    patch: { user_status: "Reject" },
    photoIds: ["photo-1", "photo-2"],
  });
  await page.getByRole("button", { name: "Set visible photos to unreviewed", exact: true }).click();
  await expect.poll(() => batchPhotoPatches.length).toBe(initialBatchPatchCount + 2);
  expect(batchPhotoPatches.at(-1)).toEqual({
    patch: { user_status: "Unreviewed" },
    photoIds: ["photo-1", "photo-2"],
  });
  await page.keyboard.press("p");
  await expect.poll(() => photoPatches.length).toBe(initialPatchCount + 4);
  expect(photoPatches.at(-1)).toEqual({ patch: { user_status: "Pick" }, photoId: "photo-1" });
  await expect(page.getByRole("heading", { name: "frame-002.jpg" })).toBeVisible();
  expect(photoListRequests).toBe(initialPhotoListRequests);
  await page.reload();
  await expect(page.getByRole("heading", { name: "frame-002.jpg" })).toBeVisible();

  await page.keyboard.press("e");
  await expect(page).toHaveURL(/\/projects\/project-1\/export$/);
  await expect(page.getByRole("heading", { name: "Export Selection" })).toBeVisible();
  await page.getByLabel("Maybe").uncheck();
  await page.getByRole("button", { name: "Export" }).click();
  await expect(page.getByText("1 photos exported.")).toBeVisible();
  await expect(page.getByText("Statuses: Pick")).toHaveCount(2);
  await expect(page.getByRole("link", { name: "Download CSV" })).toBeVisible();
  await expect(page.getByText("CSV · 1 photos")).toBeVisible();
});

test("resumes polling an active processing job on the processing page", async ({ page }) => {
  const runningJob = {
    ...completedJob,
    id: "job-running",
    status: "running",
    current_step: "hash/scoring",
    processed_items: 1,
    progress_percent: 33,
    completed_at: null,
  };

  await page.route(`**/api/projects/${project.id}/jobs`, async (route) => {
    await route.fulfill({ json: [runningJob] });
  });
  await page.route(`**/api/projects/${project.id}/jobs/${runningJob.id}`, async (route) => {
    await route.fulfill({ json: runningJob });
  });

  await page.goto(`/projects/${project.id}/process`);

  await expect(page.getByText("1 of 3 photos · 0 failed · 33%")).toBeVisible();
  await expect(page.locator("p").filter({ hasText: /^hash\/scoring$/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run Grouping and Ranking" })).toBeDisabled();
});

test("creates a project and opens the import step", async ({ page }) => {
  await page.goto("/projects/new");
  await page.getByLabel("Project name").fill("New Local Shoot");
  await page.getByRole("button", { name: "Create and Import" }).click();

  await expect(page).toHaveURL(/\/projects\/project-1\/import$/);
  await expect(page.getByRole("heading", { name: "Import Images" })).toBeVisible();
});

test("shows imported thumbnails before processing", async ({ page }) => {
  await page.goto(`/projects/${project.id}/import`);
  await page.getByLabel("Choose image files").setInputFiles({
    name: "uploaded-frame.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from([255, 216, 255, 217]),
  });

  await expect(page.getByText("1 images imported and previewed.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recently Imported" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Thumbnail for uploaded-frame.jpg" })).toBeVisible();
});

test("opens empty projects at the import step", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /Empty Shoot/ }).click();

  await expect(page).toHaveURL(/\/projects\/empty-project\/import$/);
});
