import { expect, test } from "@playwright/test";

const project = {
  id: "project-1",
  name: "E2E Shoot",
  root_path: "/tmp/framepilot/e2e",
  total_images: 2,
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
];

test.beforeEach(async ({ page }) => {
  let currentProject = { ...project };
  let currentPhotos = photos.map((photo) => ({ ...photo }));

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
    await route.fulfill({
      json: {
        id: "job-1",
        project_id: project.id,
        status: "complete",
        current_step: "complete",
        total_items: currentProject.total_images,
        processed_items: currentProject.total_images,
        error_message: null,
      },
      status: 202,
    });
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
    await route.fulfill({ json: currentPhotos });
  });

  await page.route(`**/api/projects/${project.id}/photos/*`, async (route) => {
    const photoId = route.request().url().split("/").at(-1);
    const patch = route.request().postDataJSON() as { user_status?: string; star_rating?: number };
    currentPhotos = currentPhotos.map((photo) => (photo.id === photoId ? { ...photo, ...patch } : photo));
    await route.fulfill({ json: currentPhotos.find((photo) => photo.id === photoId) });
  });

  await page.route(`**/api/projects/${project.id}/groups`, async (route) => {
    await route.fulfill({ json: groups });
  });

  await page.route(`**/api/projects/${project.id}/export`, async (route) => {
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
  await expect(page.getByRole("link", { name: "Open Culling Workspace" })).toBeVisible();

  await page.getByRole("link", { name: "Open Culling Workspace" }).click();
  await expect(page.getByRole("heading", { name: "E2E Shoot" })).toBeVisible();
  await expect(page.getByText("High confidence").first()).toBeVisible();
  await expect(page.getByText("High confidence because the top photo leads the next candidate by 0.23.")).toBeVisible();
  await page.keyboard.press("p");
  await expect(page.getByRole("heading", { name: "frame-002.jpg" })).toBeVisible();

  await page.getByRole("link", { name: "Export" }).click();
  await expect(page.getByRole("heading", { name: "Export Selection" })).toBeVisible();
  await page.getByLabel("Maybe").uncheck();
  await page.getByRole("button", { name: "Export" }).click();
  await expect(page.getByText("1 photos exported.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Download CSV" })).toBeVisible();
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
