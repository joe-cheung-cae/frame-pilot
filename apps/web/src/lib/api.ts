import { resolveApiBase } from "./apiBase.ts";

export const API_BASE = resolveApiBase();

export type Project = {
  id: string;
  name: string;
  root_path: string;
  source_mode: "copy";
  source_root_path: string | null;
  total_images: number;
  processed_images: number;
  last_processed_at: string | null;
  schema_version: number;
  created_at: string;
  updated_at: string;
  active_import_job: ProcessingJob | null;
};

export type Photo = {
  id: string;
  project_id: string;
  filename: string;
  file_ext: string | null;
  file_size: number;
  file_mtime: number | null;
  content_hash: string | null;
  project_copy_path: string | null;
  source_identity: string | null;
  width: number;
  height: number;
  capture_time: string | null;
  camera_model: string | null;
  lens_model: string | null;
  focal_length: string | null;
  aperture: string | null;
  shutter_speed: string | null;
  iso: number | null;
  thumbnail_path: string | null;
  preview_path: string | null;
  perceptual_hash: string | null;
  sharpness_score: number;
  blur_score: number;
  exposure_score: number;
  contrast_score: number;
  noise_score: number;
  face_presence: boolean;
  face_sharpness_score: number;
  eye_open_confidence: number | null;
  face_quality_score: number;
  aesthetic_score: number;
  overall_score: number;
  ai_recommendation: string;
  recommendation_explanation: string;
  user_status: "Pick" | "Maybe" | "Reject" | "Unreviewed";
  star_rating: number;
  group_id: string | null;
  processing_state: "imported" | "processing" | "processed" | "failed";
  processing_error: string | null;
};

export type PhotoStatusCounts = {
  Pick: number;
  Maybe: number;
  Reject: number;
  Unreviewed: number;
};

export type ImportResult = {
  imported: Photo[];
  skipped: { filename: string; reason: string }[];
  job?: ProcessingJob | null;
  total_files: number;
  accepted_files: number;
  skipped_files: number;
  failed_files: number;
  remaining_paths?: string[];
  expanded_total?: number | null;
  timing?: {
    total_files: number;
    imported_files: number;
    skipped_files: number;
    total_seconds: number;
    stages: Record<string, { calls: number; seconds: number }>;
  } | null;
};

export type PhotoGroup = {
  id: string;
  project_id: string;
  group_type: string;
  sequence: number;
  representative_photo_id: string | null;
  photo_count: number;
  score_summary: string;
};

export type HealthStatus = {
  status: string;
  version: string;
  service: string;
};

export type AppMeta = {
  version: string;
  service: string;
  data_dir: string;
  desktop_mode: boolean;
};

export type ProcessingJob = {
  id: string;
  project_id: string;
  job_type: string;
  status: "queued" | "running" | "complete" | "complete_with_errors" | "failed" | "cancelled";
  current_step: string;
  total_items: number;
  processed_items: number;
  failed_items: number;
  progress_percent: number;
  error_message: string | null;
  cancellation_requested: boolean;
  cancelled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  retryable: boolean;
};

export type ExportRecord = {
  id: string;
  project_id: string;
  mode: "csv" | "folder" | "zip";
  status: "running" | "complete" | "failed";
  selected_count: number;
  statuses: string;
  output_path: string;
  error_message: string | null;
  completed_at: string | null;
  created_at: string;
};

export type PhotoPatch = Partial<Pick<Photo, "user_status" | "star_rating">>;

export type ListPageOptions = {
  limit?: number;
  offset?: number;
};

export const DEFAULT_LIST_PAGE_LIMIT = 500;
export const IMPORT_UPLOAD_BATCH_SIZE = 100;
export const PHOTO_BATCH_UPDATE_SIZE = 500;

export function chunkItems<T>(items: readonly T[], size = IMPORT_UPLOAD_BATCH_SIZE): T[][] {
  if (!Number.isInteger(size) || size < 1) {
    throw new Error("Batch size must be a positive integer.");
  }
  const chunks: T[][] = [];
  for (let index = 0; index < items.length; index += size) {
    chunks.push(items.slice(index, index + size));
  }
  return chunks;
}

export type ImportPhotosOptions = {
  batchSize?: number;
  onBatchComplete?: (result: ImportResult, batchIndex: number, batchCount: number) => void;
};

export type ImportPhotosFromPathsOptions = {
  onSliceComplete?: (result: ImportResult, sliceIndex: number, expandedTotal: number) => void;
};

const IMAGE_PATH_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp"]);

function pathLooksLikeImageFile(filePath: string): boolean {
  const base = filePath.replace(/\\/g, "/").split("/").pop() ?? filePath;
  const dot = base.lastIndexOf(".");
  if (dot <= 0 || dot === base.length - 1) {
    return false;
  }
  return IMAGE_PATH_EXTENSIONS.has(base.slice(dot).toLowerCase());
}

function isLastPathImportSlice(paths: readonly string[], hasJob: boolean): boolean {
  if (paths.length === 0 || paths.length > IMPORT_UPLOAD_BATCH_SIZE) {
    return false;
  }
  // Leftover remaining_paths from the API are already expanded files.
  // A first request of picked image files is last when it fits in one slice.
  return hasJob || paths.every(pathLooksLikeImageFile);
}

export function listPageQuery(options: ListPageOptions = {}): string {
  const params = new URLSearchParams();
  if (options.limit !== undefined) {
    params.set("limit", String(options.limit));
  }
  if (options.offset !== undefined) {
    params.set("offset", String(options.offset));
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function collectPagedList<T>(
  loadPage: (options: Required<ListPageOptions>) => Promise<T[]>,
  pageLimit = DEFAULT_LIST_PAGE_LIMIT,
): Promise<T[]> {
  if (!Number.isInteger(pageLimit) || pageLimit < 1) {
    throw new Error("Page limit must be a positive integer.");
  }

  const items: T[] = [];
  let offset = 0;
  while (true) {
    const page = await loadPage({ limit: pageLimit, offset });
    items.push(...page);
    if (page.length < pageLimit) {
      return items;
    }
    offset += pageLimit;
  }
}

function formatErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String(item.msg);
        }
        return typeof item === "string" ? item : null;
      })
      .filter(Boolean);
    return messages.length ? messages.join("; ") : null;
  }
  if (detail && typeof detail === "object" && "message" in detail && typeof detail.message === "string") {
    return detail.message;
  }
  return null;
}

function errorMessageFromBody(body: string, fallback: string): string {
  if (!body) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(body) as { detail?: unknown; message?: unknown };
    return formatErrorDetail(parsed.detail) ?? (typeof parsed.message === "string" ? parsed.message : body);
  } catch {
    return body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${resolveApiBase()}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(errorMessageFromBody(text, response.statusText));
  }
  return response.json() as Promise<T>;
}

function listJobs(projectId: string, options?: ListPageOptions) {
  return request<ProcessingJob[]>(`/api/projects/${projectId}/jobs${listPageQuery(options)}`);
}

function listAllJobs(projectId: string, pageLimit?: number) {
  return collectPagedList((options) => listJobs(projectId, options), pageLimit);
}

function listPhotos(projectId: string, options?: ListPageOptions) {
  return request<Photo[]>(`/api/projects/${projectId}/photos${listPageQuery(options)}`);
}

function getPhotoStatusCounts(projectId: string) {
  return request<PhotoStatusCounts>(`/api/projects/${projectId}/photos/status-counts`);
}

function listAllPhotos(projectId: string, pageLimit?: number) {
  return collectPagedList((options) => listPhotos(projectId, options), pageLimit);
}

function listGroups(projectId: string, options?: ListPageOptions) {
  return request<PhotoGroup[]>(`/api/projects/${projectId}/groups${listPageQuery(options)}`);
}

function listAllGroups(projectId: string, pageLimit?: number) {
  return collectPagedList((options) => listGroups(projectId, options), pageLimit);
}

function listExports(projectId: string, options?: ListPageOptions) {
  return request<ExportRecord[]>(`/api/projects/${projectId}/exports${listPageQuery(options)}`);
}

function listAllExports(projectId: string, pageLimit?: number) {
  return collectPagedList((options) => listExports(projectId, options), pageLimit);
}

export const api = {
  listProjects: () => request<Project[]>("/api/projects"),
  createProject: (name: string, rootPath?: string, options?: { acknowledgeNonempty?: boolean }) => {
    const trimmedRootPath = rootPath?.trim();
    const payload: { name: string; root_path?: string; acknowledge_nonempty?: boolean } = { name };
    if (trimmedRootPath) {
      payload.root_path = trimmedRootPath;
    }
    if (options?.acknowledgeNonempty) {
      payload.acknowledge_nonempty = true;
    }
    return request<Project>("/api/projects", { method: "POST", body: JSON.stringify(payload) });
  },
  registerDesktopProjectRoot: (path: string) =>
    request<{ path: string }>("/api/desktop/project-roots", {
      method: "POST",
      body: JSON.stringify({ path }),
    }),
  getHealth: () => request<HealthStatus>("/api/health"),
  getMeta: () => request<AppMeta>("/api/meta"),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  getPhoto: (projectId: string, photoId: string) => request<Photo>(`/api/projects/${projectId}/photos/${photoId}`),
  importPhotosBatch: (
    projectId: string,
    files: readonly File[],
    options: {
      jobId?: string | null;
      expectedTotal?: number;
      finalize?: boolean;
    } = {},
  ) => {
    const body = new FormData();
    files.forEach((file) => body.append("files", file));
    if (options.jobId) {
      body.append("job_id", options.jobId);
    }
    if (options.expectedTotal !== undefined) {
      body.append("expected_total", String(options.expectedTotal));
    }
    if (options.finalize !== undefined) {
      body.append("finalize", options.finalize ? "true" : "false");
    }
    return request<ImportResult>(`/api/projects/${projectId}/imports`, { method: "POST", body });
  },
  importPhotos: async (projectId: string, files: readonly File[], options: ImportPhotosOptions = {}) => {
    if (!files.length) {
      throw new Error("At least one file is required.");
    }
    const batches = chunkItems(files, options.batchSize ?? IMPORT_UPLOAD_BATCH_SIZE);
    let jobId: string | undefined;
    const imported: ImportResult["imported"] = [];
    const skipped: ImportResult["skipped"] = [];
    let lastResult: ImportResult | null = null;

    for (let batchIndex = 0; batchIndex < batches.length; batchIndex += 1) {
      const batch = batches[batchIndex];
      const isLast = batchIndex === batches.length - 1;
      const result = await api.importPhotosBatch(projectId, batch, {
        jobId,
        expectedTotal: files.length,
        finalize: isLast,
      });
      jobId = result.job?.id ?? jobId;
      imported.push(...result.imported);
      skipped.push(...result.skipped);
      lastResult = result;
      options.onBatchComplete?.(result, batchIndex, batches.length);
    }

    if (!lastResult) {
      throw new Error("Import did not return a result.");
    }

    return {
      ...lastResult,
      imported,
      skipped,
      total_files: files.length,
      accepted_files: imported.length,
      skipped_files: skipped.length,
      failed_files: skipped.length,
    } satisfies ImportResult;
  },
  importPhotosFromPathsBatch: (
    projectId: string,
    paths: readonly string[],
    options: {
      jobId?: string | null;
      expectedTotal?: number | null;
      finalize?: boolean;
    } = {},
  ) =>
    request<ImportResult>(`/api/projects/${projectId}/imports/from-paths`, {
      method: "POST",
      body: JSON.stringify({
        paths: [...paths],
        job_id: options.jobId ?? null,
        expected_total: options.expectedTotal ?? null,
        finalize: options.finalize ?? true,
      }),
    }),
  importPhotosFromPaths: async (
    projectId: string,
    paths: readonly string[],
    options: ImportPhotosFromPathsOptions = {},
  ) => {
    if (!paths.length) {
      throw new Error("At least one path is required.");
    }

    let currentPaths = [...paths];
    let jobId: string | undefined;
    let expectedTotal: number | undefined;
    const imported: ImportResult["imported"] = [];
    const skipped: ImportResult["skipped"] = [];
    let lastResult: ImportResult | null = null;
    let sliceIndex = 0;

    while (currentPaths.length > 0) {
      const isLastSlice = isLastPathImportSlice(currentPaths, jobId !== undefined);
      const result = await api.importPhotosFromPathsBatch(projectId, currentPaths, {
        jobId,
        expectedTotal,
        finalize: isLastSlice,
      });
      jobId = result.job?.id ?? jobId;
      expectedTotal = result.expanded_total ?? expectedTotal;
      imported.push(...result.imported);
      skipped.push(...result.skipped);
      lastResult = result;
      const progressTotal = expectedTotal ?? result.imported.length;
      options.onSliceComplete?.(result, sliceIndex, progressTotal);
      sliceIndex += 1;

      const remainingPaths = result.remaining_paths ?? [];
      if (remainingPaths.length === 0) {
        if (!isLastSlice) {
          const finalized = await api.importPhotosFromPathsBatch(projectId, [], {
            jobId,
            expectedTotal,
            finalize: true,
          });
          jobId = finalized.job?.id ?? jobId;
          expectedTotal = finalized.expanded_total ?? expectedTotal;
          lastResult = finalized;
          options.onSliceComplete?.(
            {
              ...finalized,
              imported,
              skipped,
              remaining_paths: [],
              expanded_total: expectedTotal ?? finalized.expanded_total,
            },
            sliceIndex,
            expectedTotal ?? progressTotal,
          );
        }
        break;
      }
      currentPaths = remainingPaths;
    }

    if (!lastResult) {
      throw new Error("Import did not return a result.");
    }

    return {
      ...lastResult,
      imported,
      skipped,
      remaining_paths: [],
      expanded_total: expectedTotal ?? lastResult.expanded_total ?? null,
      total_files: expectedTotal ?? imported.length,
      accepted_files: imported.length,
      skipped_files: skipped.length,
      failed_files: skipped.length,
    } satisfies ImportResult;
  },
  processProject: (projectId: string) =>
    request<ProcessingJob>(`/api/projects/${projectId}/process`, { method: "POST" }),
  listJobs,
  listAllJobs,
  getJob: (projectId: string, jobId: string) => request<ProcessingJob>(`/api/projects/${projectId}/jobs/${jobId}`),
  cancelJob: (projectId: string, jobId: string) =>
    request<ProcessingJob>(`/api/projects/${projectId}/jobs/${jobId}/cancel`, { method: "POST" }),
  retryJob: (projectId: string, jobId: string) =>
    request<ProcessingJob>(`/api/projects/${projectId}/jobs/${jobId}/retry`, { method: "POST" }),
  listPhotos,
  getPhotoStatusCounts,
  listAllPhotos,
  updatePhoto: (projectId: string, photoId: string, patch: PhotoPatch) =>
    request<Photo>(`/api/projects/${projectId}/photos/${photoId}`, { method: "PATCH", body: JSON.stringify(patch) }),
  batchUpdatePhotos: async (projectId: string, photoIds: string[], patch: PhotoPatch) => {
    const batches = chunkItems(photoIds, PHOTO_BATCH_UPDATE_SIZE);
    const updated: Photo[] = [];
    for (const batch of batches) {
      const page = await request<Photo[]>(`/api/projects/${projectId}/photos/batch`, {
        method: "PATCH",
        body: JSON.stringify({ photo_ids: batch, ...patch }),
      });
      updated.push(...page);
    }
    return updated;
  },
  listGroups,
  listAllGroups,
  listExports,
  listAllExports,
  exportSelection: (projectId: string, mode: "csv" | "folder" | "zip", statuses: string[]) =>
    request<ExportRecord>(`/api/projects/${projectId}/exports`, {
      method: "POST",
      body: JSON.stringify({ mode, statuses }),
    }),
};

export function exportDownloadUrl(projectId: string, exportId: string): string {
  return `${resolveApiBase()}/api/projects/${projectId}/exports/${exportId}/download`;
}

export function assetUrl(projectId: string, path: string | null): string | null {
  if (!path) {
    return null;
  }
  const normalized = path.replace(/\\/g, "/");
  const parts = normalized.split("/").filter(Boolean);
  const filename = parts.at(-1);
  const kind = parts.at(-2);
  if (!filename || !kind) {
    return null;
  }
  return `${resolveApiBase()}/api/assets/${projectId}/${encodeURIComponent(kind)}/${encodeURIComponent(filename)}`;
}
