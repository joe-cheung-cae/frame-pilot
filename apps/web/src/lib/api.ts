export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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
};

export type PhotoGroup = {
  id: string;
  project_id: string;
  group_type: string;
  representative_photo_id: string | null;
  photo_count: number;
  score_summary: string;
};

export type ProcessingJob = {
  id: string;
  project_id: string;
  job_type: string;
  status: "queued" | "running" | "complete" | "failed";
  current_step: string;
  total_items: number;
  processed_items: number;
  failed_items: number;
  progress_percent: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
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
  const response = await fetch(`${API_BASE}${path}`, {
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
  createProject: (name: string, rootPath?: string) => {
    const trimmedRootPath = rootPath?.trim();
    const payload: { name: string; root_path?: string } = { name };
    if (trimmedRootPath) {
      payload.root_path = trimmedRootPath;
    }
    return request<Project>("/api/projects", { method: "POST", body: JSON.stringify(payload) });
  },
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  importPhotos: (projectId: string, files: FileList) => {
    const body = new FormData();
    Array.from(files).forEach((file) => body.append("files", file));
    return request<ImportResult>(`/api/projects/${projectId}/imports`, { method: "POST", body });
  },
  processProject: (projectId: string) =>
    request<ProcessingJob>(`/api/projects/${projectId}/process`, { method: "POST" }),
  listJobs,
  listAllJobs,
  getJob: (projectId: string, jobId: string) =>
    request<ProcessingJob>(`/api/projects/${projectId}/jobs/${jobId}`),
  listPhotos,
  getPhotoStatusCounts,
  listAllPhotos,
  updatePhoto: (projectId: string, photoId: string, patch: PhotoPatch) =>
    request<Photo>(`/api/projects/${projectId}/photos/${photoId}`, { method: "PATCH", body: JSON.stringify(patch) }),
  batchUpdatePhotos: (projectId: string, photoIds: string[], patch: PhotoPatch) =>
    request<Photo[]>(`/api/projects/${projectId}/photos/batch`, {
      method: "PATCH",
      body: JSON.stringify({ photo_ids: photoIds, ...patch }),
    }),
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
  return `${API_BASE}/api/projects/${projectId}/exports/${exportId}/download`;
}

export function assetUrl(projectId: string, path: string | null): string | null {
  if (!path) {
    return null;
  }
  const parts = path.split("/");
  const filename = parts.at(-1);
  const kind = parts.at(-2);
  if (!filename || !kind) {
    return null;
  }
  return `${API_BASE}/api/assets/${projectId}/${kind}/${filename}`;
}
