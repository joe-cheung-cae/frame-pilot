import { expect, test } from "@playwright/test";

const project = {
  id: "project-1",
  name: "E2E Shoot",
  root_path: "/tmp/framepilot/e2e",
  source_mode: "copy",
  source_root_path: null,
  total_images: 3,
  processed_images: 0,
  last_processed_at: null,
  schema_version: 2,
  created_at: "2026-06-02T00:00:00Z",
  updated_at: "2026-06-02T00:00:00Z",
};

const emptyProject = {
  ...project,
  id: "empty-project",
  name: "Empty Shoot",
  root_path: "/tmp/framepilot/empty-e2e",
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
    capture_time: "2026-01-02T03:04:05",
    camera_model: "FramePilotCam",
    lens_model: "FramePilot 35mm",
    focal_length: "35",
    aperture: "2.8",
    shutter_speed: "1/125",
    iso: 400,
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
let failNextPhotoPatch = false;
let failExportHistory = false;
let failNextExport = false;
let failPhotoStatusCounts = false;
let failJobList = false;
let failJobDetail = false;
let failProjectList = false;
let failProjectDetail = false;
let failNextImport = false;
let skipNextImport = false;
let skipManyNextImport = false;
let failPreviewAssets = false;
let photoListRequests = 0;
let photoListRequestUrls: string[] = [];
let projectCreatePayloads: { name?: string; root_path?: string }[] = [];

function projectListRoute(resource: "exports" | "groups" | "jobs" | "photos") {
  return new RegExp(`/api/projects/${project.id}/${resource}(?:\\?.*)?$`);
}

function photoStatusCounts(currentPhotos: readonly { user_status: string }[]) {
  return currentPhotos.reduce(
    (counts, photo) => {
      if (photo.user_status in counts) {
        counts[photo.user_status as keyof typeof counts] += 1;
      }
      return counts;
    },
    { Pick: 0, Maybe: 0, Reject: 0, Unreviewed: 0 },
  );
}

test.beforeEach(async ({ page }) => {
  photoPatches = [];
  batchPhotoPatches = [];
  failNextPhotoPatch = false;
  failExportHistory = false;
  failNextExport = false;
  failPhotoStatusCounts = false;
  failJobList = false;
  failJobDetail = false;
  failProjectList = false;
  failProjectDetail = false;
  failNextImport = false;
  skipNextImport = false;
  skipManyNextImport = false;
  failPreviewAssets = false;
  photoListRequests = 0;
  photoListRequestUrls = [];
  projectCreatePayloads = [];
  let currentProject = { ...project };
  let currentPhotos = photos.map((photo) => ({ ...photo }));
  let currentJob: typeof completedJob | null = null;

  await page.route("**/api/projects", async (route) => {
    if (route.request().method() === "POST") {
      const payload = route.request().postDataJSON() as { name?: string; root_path?: string };
      projectCreatePayloads.push(payload);
      currentProject = {
        ...currentProject,
        name: payload.name ?? currentProject.name,
        root_path: payload.root_path?.trim() || currentProject.root_path,
        total_images: 0,
        processed_images: 0,
      };
      await route.fulfill({ json: currentProject, status: 201 });
      return;
    }
    if (failProjectList) {
      await route.fulfill({ json: { detail: "Could not read local project database" }, status: 500 });
      return;
    }
    await route.fulfill({ json: [currentProject, emptyProject] });
  });

  await page.route(`**/api/projects/${project.id}`, async (route) => {
    if (failProjectDetail) {
      await route.fulfill({ json: { detail: "Could not load project details" }, status: 500 });
      return;
    }
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

  await page.route(projectListRoute("jobs"), async (route) => {
    if (failJobList) {
      await route.fulfill({ json: { detail: "Could not load processing jobs" }, status: 500 });
      return;
    }
    await route.fulfill({ json: currentJob ? [currentJob] : [] });
  });

  await page.route(`**/api/projects/${project.id}/jobs/*`, async (route) => {
    if (failJobDetail) {
      failJobDetail = false;
      await route.fulfill({ json: { detail: "Processing job status endpoint failed" }, status: 500 });
      return;
    }
    const jobId = route.request().url().split("/").at(-1);
    if (currentJob?.id !== jobId) {
      await route.fulfill({ json: { detail: "Processing job not found" }, status: 404 });
      return;
    }
    await route.fulfill({ json: currentJob });
  });

  await page.route(`**/api/projects/${project.id}/imports`, async (route) => {
    if (failNextImport) {
      failNextImport = false;
      await route.fulfill({ json: { detail: "Every selected file was skipped" }, status: 422 });
      return;
    }
    currentProject = { ...currentProject, total_images: currentProject.total_images + 1, processed_images: 0 };
    const imported = {
      ...photos[0],
      id: "imported-photo",
      filename: "uploaded-frame.jpg",
      thumbnail_path: "thumbnails/uploaded-frame.webp",
      preview_path: "previews/uploaded-frame.webp",
    };
    currentPhotos = [imported, ...currentPhotos];
    const skipped = skipNextImport
      ? skipManyNextImport
        ? Array.from({ length: 7 }, (_value, index) => ({
            filename: `unsupported-${index + 1}.txt`,
            reason: "Only JPEG, PNG, and WebP files are supported",
          }))
        : [{ filename: "notes.txt", reason: "Only JPEG, PNG, and WebP files are supported" }]
      : [];
    skipNextImport = false;
    skipManyNextImport = false;
    await route.fulfill({ json: { imported: [imported], skipped }, status: 201 });
  });

  await page.route(projectListRoute("photos"), async (route) => {
    photoListRequests += 1;
    photoListRequestUrls.push(route.request().url());
    const url = new URL(route.request().url());
    const limitParam = url.searchParams.get("limit");
    const offset = Number(url.searchParams.get("offset") ?? 0);
    const limit = limitParam ? Number(limitParam) : currentPhotos.length;
    await route.fulfill({ json: currentPhotos.slice(offset, offset + limit) });
  });

  await page.route(`**/api/projects/${project.id}/photos/status-counts`, async (route) => {
    if (failPhotoStatusCounts) {
      await route.fulfill({ json: { detail: "Could not load exportable photos" }, status: 500 });
      return;
    }
    await route.fulfill({ json: photoStatusCounts(currentPhotos) });
  });

  await page.route(`**/api/projects/${project.id}/photos/*`, async (route) => {
    if (route.request().url().endsWith("/photos/batch") || route.request().url().endsWith("/photos/status-counts")) {
      await route.fallback();
      return;
    }
    if (failNextPhotoPatch) {
      failNextPhotoPatch = false;
      await route.fulfill({ json: { detail: "Could not save review update" }, status: 500 });
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

  await page.route(projectListRoute("groups"), async (route) => {
    await route.fulfill({ json: groups });
  });

  await page.route(projectListRoute("exports"), async (route) => {
    if (route.request().method() === "GET") {
      if (failExportHistory) {
        await route.fulfill({ json: { detail: "Could not load export history" }, status: 500 });
        return;
      }
      await route.fulfill({ json: [] });
      return;
    }
    if (failNextExport) {
      failNextExport = false;
      await route.fulfill({ json: { detail: "Export failed" }, status: 500 });
      return;
    }
    const payload = route.request().postDataJSON() as { mode?: "csv" | "folder" | "zip"; statuses?: string[] };
    const exportMode = payload.mode ?? "csv";
    const exportOutputPath =
      exportMode === "folder"
        ? `${currentProject.root_path}/exports/folders/selected-export-1`
        : `${currentProject.root_path}/exports/${exportMode}/selection-export-1.${exportMode}`;
    const selectedStatuses = payload.statuses ?? ["Pick"];

    await route.fulfill({
      json: {
        id: "export-1",
        project_id: project.id,
        mode: exportMode,
        status: "complete",
        selected_count: currentPhotos.filter((photo) => selectedStatuses.includes(photo.user_status)).length,
        statuses: JSON.stringify(selectedStatuses),
        output_path: exportOutputPath,
        created_at: "2026-06-02T00:00:00Z",
      },
      status: 201,
    });
  });

  await page.route("**/api/assets/**", async (route) => {
    if (failPreviewAssets && route.request().url().includes("/previews/frame-001.webp")) {
      await route.fulfill({ json: { detail: "Asset not found" }, status: 404 });
      return;
    }
    await route.fulfill({
      body: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lK3wLwAAAABJRU5ErkJggg==",
        "base64",
      ),
      contentType: "image/png",
    });
  });
});

test("shows culling save errors when a rating update fails", async ({ page }) => {
  await page.goto(`/projects/${project.id}/cull`);
  await expect(page.getByRole("heading", { name: "frame-001.jpg" })).toBeVisible();

  failNextPhotoPatch = true;
  await page.keyboard.press("5");

  await expect(page.getByText("Could not save review update")).toBeVisible();
  await expect.poll(() => photoPatches.length).toBe(0);
});

test("shows project list load errors", async ({ page }) => {
  failProjectList = true;

  await page.goto("/");

  await expect(page.getByText("Could not load projects: Could not read local project database")).toBeVisible();
});

test("opens keyboard shortcuts help from the shell", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Help" }).click();

  await expect(page).toHaveURL(/\/help$/);
  await expect(page.getByRole("heading", { name: "Keyboard Shortcuts" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Navigation" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Review" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Workspace" })).toBeVisible();
  await expect(page.getByText("Left Arrow")).toBeVisible();
  await expect(page.getByText("Mark Pick")).toBeVisible();
  await expect(page.getByText("Toggle compare")).toBeVisible();
  await expect(page.getByText("Open export")).toBeVisible();
});

test("uses local settings for default export statuses", async ({ page }) => {
  await page.goto("/settings");

  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  await expect(page.getByLabel("Pick")).toBeChecked();
  await expect(page.getByLabel("Maybe")).toBeChecked();

  await page.getByLabel("Maybe").uncheck();

  await expect(page.getByText("Saved locally.")).toBeVisible();

  await page.goto(`/projects/${project.id}/export`);

  await expect(page.getByLabel("Pick")).toBeChecked();
  await expect(page.getByLabel("Maybe")).not.toBeChecked();
});

test("shows culling workspace load errors", async ({ page }) => {
  failProjectDetail = true;

  await page.goto(`/projects/${project.id}/cull`);

  await expect(page.getByText("Could not load this project: Could not load project details")).toBeVisible();
});

test("shows culling preview asset load errors", async ({ page }) => {
  failPreviewAssets = true;

  await page.goto(`/projects/${project.id}/cull`);

  await expect(page.getByRole("heading", { name: "frame-001.jpg" })).toBeVisible();
  await expect(page.getByText("Preview failed to load.")).toBeVisible();
});

test("shows export history load errors", async ({ page }) => {
  failExportHistory = true;

  await page.goto(`/projects/${project.id}/export`);

  await expect(page.getByText("Could not load export history")).toBeVisible();
  await expect(page.getByText("No exports yet.")).toHaveCount(0);
});

test("shows export project load errors", async ({ page }) => {
  failProjectDetail = true;

  await page.goto(`/projects/${project.id}/export`);

  await expect(page.getByText("Could not load project details")).toBeVisible();
});

test("loads more export history on request", async ({ page }) => {
  const requestedLimits: number[] = [];
  const exportHistory = Array.from({ length: 51 }, (_, index) => {
    const exportNumber = String(index + 1).padStart(3, "0");
    return {
      id: `export-${exportNumber}`,
      project_id: project.id,
      mode: "csv",
      status: "complete",
      selected_count: 1,
      statuses: '["Pick"]',
      output_path: `/tmp/framepilot/e2e/exports/history-${exportNumber}.csv`,
      error_message: null,
      completed_at: "2026-06-02T00:00:00Z",
      created_at: "2026-06-02T00:00:00Z",
    };
  });

  await page.unroute(projectListRoute("exports"));
  await page.route(projectListRoute("exports"), async (route) => {
    const url = new URL(route.request().url());
    const limit = Number(url.searchParams.get("limit") ?? exportHistory.length);
    const offset = Number(url.searchParams.get("offset") ?? 0);
    requestedLimits.push(limit);
    await route.fulfill({ json: exportHistory.slice(offset, offset + limit) });
  });

  await page.goto(`/projects/${project.id}/export`);

  await expect(page.getByText("/tmp/framepilot/e2e/exports/history-050.csv")).toBeVisible();
  await expect(page.getByText("/tmp/framepilot/e2e/exports/history-051.csv")).toHaveCount(0);
  expect(requestedLimits[0]).toBe(50);

  await page.getByRole("button", { name: "Load more exports" }).click();

  await expect.poll(() => requestedLimits.includes(100)).toBe(true);
  await expect(page.getByText("/tmp/framepilot/e2e/exports/history-051.csv")).toBeVisible();
});

test("shows export photo count load errors", async ({ page }) => {
  failPhotoStatusCounts = true;

  await page.goto(`/projects/${project.id}/export`);

  await expect(page.getByText("Could not load exportable photos")).toBeVisible();
  await expect(page.getByText("No photos match the selected statuses.")).toHaveCount(0);
});

test("shows export creation errors", async ({ page }) => {
  await page.goto(`/projects/${project.id}/cull`);
  await expect(page.getByRole("heading", { name: "frame-001.jpg" })).toBeVisible();
  await page.keyboard.press("p");
  await expect.poll(() => photoPatches.length).toBe(1);

  failNextExport = true;
  await page.goto(`/projects/${project.id}/export`);
  await page.getByLabel("Maybe").uncheck();
  await page.getByRole("button", { name: "Export" }).click();

  await expect(page.getByText("Export failed")).toBeVisible();
});

test("copies folder export output paths", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (text: string) => {
          window.localStorage.setItem("copied-export-path", text);
        },
      },
    });
  });
  const folderPath = `${project.root_path}/exports/folders/selected-export-1`;

  await page.goto(`/projects/${project.id}/cull`);
  await expect(page.getByRole("heading", { name: "frame-001.jpg" })).toBeVisible();
  await page.keyboard.press("p");
  await expect.poll(() => photoPatches.length).toBe(1);

  await page.goto(`/projects/${project.id}/export`);
  await page.getByLabel("Maybe").uncheck();
  await page.getByRole("button", { name: "Folder" }).click();
  await page.getByRole("button", { name: "Export" }).click();

  await expect(page.getByText(`1 photo exported to ${folderPath}`)).toBeVisible();
  await page.getByRole("button", { name: "Copy Path" }).first().click();

  await expect(page.getByRole("button", { name: "Path Copied" }).first()).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.localStorage.getItem("copied-export-path"))).toBe(folderPath);
});

test("shows processing job list load errors", async ({ page }) => {
  failJobList = true;

  await page.goto(`/projects/${project.id}/process`);

  await expect(page.getByText("Could not load processing jobs")).toBeVisible();
});

test("shows processing project load errors", async ({ page }) => {
  failProjectDetail = true;

  await page.goto(`/projects/${project.id}/process`);

  await expect(page.getByText("Could not load project details")).toBeVisible();
});

test("shows project dashboard load errors", async ({ page }) => {
  failProjectDetail = true;

  await page.goto(`/projects/${project.id}`);

  await expect(page.getByText("Could not load project details")).toBeVisible();
});

test("shows processing job polling errors", async ({ page }) => {
  failJobDetail = true;
  await page.goto(`/projects/${project.id}/process`);

  await page.getByRole("button", { name: "Run Grouping and Ranking" }).click();

  await expect(
    page.getByText("Could not load processing job status: Processing job status endpoint failed"),
  ).toBeVisible();
});

test("loads more processing history on request", async ({ page }) => {
  const requestedLimits: number[] = [];
  const jobHistory = Array.from({ length: 51 }, (_, index) => {
    const jobNumber = String(index + 1).padStart(3, "0");
    return {
      ...completedJob,
      id: `history-job-${jobNumber}`,
      current_step: `history-step-${jobNumber}`,
    };
  });

  await page.unroute(projectListRoute("jobs"));
  await page.route(projectListRoute("jobs"), async (route) => {
    const url = new URL(route.request().url());
    const limit = Number(url.searchParams.get("limit") ?? jobHistory.length);
    const offset = Number(url.searchParams.get("offset") ?? 0);
    requestedLimits.push(limit);
    await route.fulfill({ json: jobHistory.slice(offset, offset + limit) });
  });

  await page.goto(`/projects/${project.id}/process`);

  await expect(page.getByText("history-step-050")).toBeVisible();
  await expect(page.getByText("history-step-051")).toHaveCount(0);
  expect(requestedLimits[0]).toBe(50);

  await page.getByRole("button", { name: "Load more jobs" }).click();

  await expect.poll(() => requestedLimits.includes(100)).toBe(true);
  await expect(page.getByText("history-step-051")).toBeVisible();
});

test("walks the local project review and export flow in a browser", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Recent Projects" })).toBeVisible();
  await expect(page.getByText(/Project data: \/tmp\/framepilot\/e2e/)).toBeVisible();
  await expect(page.getByRole("link", { name: /Next: Process photos/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /Next: Import images/ })).toBeVisible();
  await page.getByRole("link", { name: "Dashboard" }).first().click();
  await expect(page).toHaveURL(/\/projects\/project-1$/);
  await expect(page.getByRole("heading", { name: "E2E Shoot" })).toBeVisible();
  await expect(page.getByText("0 of 3 photos processed")).toBeVisible();
  await expect(page.getByText(`Project data: ${project.root_path}`)).toBeVisible();
  await expect(page.getByRole("link", { name: "Import", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Process", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Cull", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Export", exact: true })).toBeVisible();
  await page.goto("/");
  await page.getByRole("link", { name: /E2E Shoot/ }).click();
  await expect(page).toHaveURL(/\/projects\/project-1\/process$/);

  await page.goto(`/projects/${project.id}/process`);
  await page.getByRole("button", { name: "Run Grouping and Ranking" }).click();
  await expect(page.getByText("3 of 3 photos · 0 failed · 100%").first()).toBeVisible();
  await expect(page.locator("p").filter({ hasText: /^complete$/ }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Open Culling Workspace" })).toBeVisible();

  await page.getByRole("link", { name: "Open Culling Workspace" }).click();
  await expect(page.getByRole("heading", { name: "E2E Shoot" })).toBeVisible();
  expect(photoListRequestUrls.some((url) => url.includes("limit=500") && url.includes("offset=0"))).toBe(true);
  await expect(page.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Picks" })).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("button", { name: "Group 1, 2 photos, High confidence" })).toHaveAttribute(
    "aria-current",
    "true",
  );
  await expect(page.getByRole("button", { name: "Select frame-001.jpg" })).toHaveAttribute("aria-current", "true");
  await expect(page.getByRole("button", { name: "Toggle large preview" })).toHaveAttribute("aria-pressed", "false");
  await page.keyboard.press("Space");
  await expect(page.getByRole("button", { name: "Toggle large preview" })).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Space");
  await expect(page.getByRole("button", { name: "Toggle large preview" })).toHaveAttribute("aria-pressed", "false");
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
  await expect(page.getByRole("button", { name: "Group 2, 1 photo, Low confidence" })).toHaveAttribute(
    "aria-current",
    "true",
  );
  await expect(page.getByText("Low confidence because this group has no similar alternative to compare.")).toBeVisible();
  await page.keyboard.press("ArrowUp");
  await expect(page.getByRole("heading", { name: "frame-001.jpg" })).toBeVisible();
  await expect(page.getByText("FramePilotCam")).toBeVisible();
  await expect(page.getByText("FramePilot 35mm")).toBeVisible();
  await expect(page.getByText("f/2.8")).toBeVisible();
  await expect(page.getByText("1/125")).toBeVisible();
  const initialPatchCount = photoPatches.length;
  const initialPhotoListRequests = photoListRequests;
  await expect(page.getByRole("button", { name: "Set active photo to Unreviewed" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByRole("button", { name: "Clear rating" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "5 stars" })).toHaveAttribute("aria-pressed", "false");
  await page.keyboard.press("5");
  await expect.poll(() => photoPatches.length).toBe(initialPatchCount + 1);
  expect(photoPatches.at(-1)).toEqual({ patch: { star_rating: 5 }, photoId: "photo-1" });
  await expect(page.getByRole("button", { name: "5 stars" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Clear rating" }).click();
  await expect.poll(() => photoPatches.length).toBe(initialPatchCount + 2);
  expect(photoPatches.at(-1)).toEqual({ patch: { star_rating: 0 }, photoId: "photo-1" });
  await expect(page.getByRole("button", { name: "Clear rating" })).toHaveAttribute("aria-pressed", "true");
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
  await expect(page.getByText(`Exports folder: ${project.root_path}/exports`)).toBeVisible();
  await page.getByLabel("Maybe").uncheck();
  await page.getByRole("button", { name: "Export" }).click();
  await expect(page.getByText("1 photo exported.")).toBeVisible();
  await expect(page.getByText("Statuses: Pick")).toHaveCount(2);
  await expect(page.getByRole("link", { name: "Download CSV" })).toBeVisible();
  await expect(page.getByText("CSV · 1 photo")).toBeVisible();
});

test("loads the full culling photo list only on request", async ({ page }) => {
  const manyPhotos = Array.from({ length: 501 }, (_, index) => ({
    ...photos[index % photos.length],
    id: `large-photo-${index + 1}`,
    filename: `large-frame-${String(index + 1).padStart(3, "0")}.jpg`,
    group_id: "group-1",
  }));
  const requestedOffsets: number[] = [];

  await page.unroute(`**/api/projects/${project.id}`);
  await page.unroute(projectListRoute("photos"));
  await page.route(`**/api/projects/${project.id}`, async (route) => {
    await route.fulfill({
      json: { ...project, total_images: manyPhotos.length, processed_images: manyPhotos.length },
    });
  });
  await page.route(projectListRoute("photos"), async (route) => {
    const url = new URL(route.request().url());
    const limit = Number(url.searchParams.get("limit") ?? manyPhotos.length);
    const offset = Number(url.searchParams.get("offset") ?? 0);
    requestedOffsets.push(offset);
    await route.fulfill({ json: manyPhotos.slice(offset, offset + limit) });
  });

  await page.goto(`/projects/${project.id}/cull`);

  await expect(page.getByRole("heading", { name: "large-frame-001.jpg" })).toBeVisible();
  await expect(page.getByText("500 of 501 loaded")).toBeVisible();
  expect(requestedOffsets).toEqual([0]);

  await page.getByRole("button", { name: "Load all photos" }).click();

  await expect.poll(() => requestedOffsets).toEqual([0, 0, 500]);
  await expect(page.getByText("500 of 501 loaded")).toHaveCount(0);
  await expect(page.getByText("0/501 loaded reviewed")).toBeVisible();
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

  await page.route(projectListRoute("jobs"), async (route) => {
    await route.fulfill({ json: [runningJob] });
  });
  await page.route(`**/api/projects/${project.id}/jobs/${runningJob.id}`, async (route) => {
    await route.fulfill({ json: runningJob });
  });

  await page.goto(`/projects/${project.id}/process`);

  await expect(page.getByText("1 of 3 photos · 0 failed · 33%").first()).toBeVisible();
  await expect(page.locator("p").filter({ hasText: /^hash\/scoring$/ }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Run Grouping and Ranking" })).toBeDisabled();
});

test("creates a project and opens the import step", async ({ page }) => {
  await page.goto("/projects/new");
  await page.getByLabel("Project name").fill("New Local Shoot");
  await page.getByRole("button", { name: "Create and Import" }).click();

  await expect(page).toHaveURL(/\/projects\/project-1\/import$/);
  await expect(page.getByRole("heading", { name: "Import Images" })).toBeVisible();
  expect(projectCreatePayloads).toEqual([{ name: "New Local Shoot" }]);
});

test("creates a project with a custom local data folder", async ({ page }) => {
  const customRootPath = "/tmp/framepilot/custom-e2e";

  await page.goto("/projects/new");
  await page.getByLabel("Project name").fill("Custom Storage Shoot");
  await page.getByLabel("Project data folder").fill(customRootPath);
  await page.getByRole("button", { name: "Create and Import" }).click();

  await expect(page).toHaveURL(/\/projects\/project-1\/import$/);
  await expect(page.getByRole("heading", { name: "Import Images" })).toBeVisible();
  await expect(page.getByText(`Project data: ${customRootPath}`)).toBeVisible();
  expect(projectCreatePayloads).toEqual([{ name: "Custom Storage Shoot", root_path: customRootPath }]);
});

test("shows imported thumbnails before processing", async ({ page }) => {
  await page.goto(`/projects/${project.id}/import`);
  await expect(page.getByText(`Project data: ${project.root_path}`)).toBeVisible();
  await expect(page.getByText("Source folders are not tracked for rescan yet.")).toBeVisible();
  await page.getByLabel("Choose image files").setInputFiles({
    name: "uploaded-frame.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from([255, 216, 255, 217]),
  });

  await expect(page.getByText("1 image imported and previewed.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recently Imported" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Thumbnail for uploaded-frame.jpg" })).toBeVisible();
});

test("shows skipped files after a mixed import", async ({ page }) => {
  skipNextImport = true;
  await page.goto(`/projects/${project.id}/import`);

  await page.getByLabel("Choose image files").setInputFiles({
    name: "uploaded-frame.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from([255, 216, 255, 217]),
  });

  await expect(page.getByText("1 image imported and previewed.")).toBeVisible();
  await expect(page.getByText("1 file skipped.")).toBeVisible();
  await expect(page.getByText("notes.txt: Only JPEG, PNG, and WebP files are supported")).toBeVisible();
});

test("expands long skipped file lists after import", async ({ page }) => {
  skipNextImport = true;
  skipManyNextImport = true;
  await page.goto(`/projects/${project.id}/import`);

  await page.getByLabel("Choose image files").setInputFiles({
    name: "uploaded-frame.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from([255, 216, 255, 217]),
  });

  await expect(page.getByText("7 files skipped.")).toBeVisible();
  await expect(page.getByText("unsupported-1.txt: Only JPEG, PNG, and WebP files are supported")).toBeVisible();
  await expect(page.getByText("unsupported-6.txt: Only JPEG, PNG, and WebP files are supported")).toHaveCount(0);

  await page.getByRole("button", { name: "Show all 7 skipped files" }).click();

  await expect(page.getByText("unsupported-6.txt: Only JPEG, PNG, and WebP files are supported")).toBeVisible();
  await expect(page.getByRole("button", { name: "Show first 5 skipped files" })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
});

test("clears stale import results when a later import fails", async ({ page }) => {
  await page.goto(`/projects/${project.id}/import`);
  await page.getByLabel("Choose image files").setInputFiles({
    name: "uploaded-frame.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from([255, 216, 255, 217]),
  });
  await expect(page.getByRole("heading", { name: "Recently Imported" })).toBeVisible();

  failNextImport = true;
  await page.getByLabel("Choose image files").setInputFiles({
    name: "unsupported.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from("not an image"),
  });

  await expect(page.getByText("Every selected file was skipped")).toBeVisible();
  await expect(page.getByText("1 image imported and previewed.")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Recently Imported" })).toHaveCount(0);
});

test("shows import project load errors", async ({ page }) => {
  failProjectDetail = true;

  await page.goto(`/projects/${project.id}/import`);

  await expect(page.getByText("Could not load project details")).toBeVisible();
});

test("opens empty projects at the import step", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /Empty Shoot/ }).click();

  await expect(page).toHaveURL(/\/projects\/empty-project\/import$/);
});
