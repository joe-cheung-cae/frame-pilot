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

export const api = {
  listProjects: () => request<Project[]>("/api/projects"),
  createProject: (name: string) =>
    request<Project>("/api/projects", { method: "POST", body: JSON.stringify({ name }) }),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  importPhotos: (projectId: string, files: FileList) => {
    const body = new FormData();
    Array.from(files).forEach((file) => body.append("files", file));
    return request<ImportResult>(`/api/projects/${projectId}/import`, { method: "POST", body });
  },
  processProject: (projectId: string) =>
    request<ProcessingJob>(`/api/projects/${projectId}/process`, { method: "POST" }),
  listJobs: (projectId: string) => request<ProcessingJob[]>(`/api/projects/${projectId}/jobs`),
  getJob: (projectId: string, jobId: string) =>
    request<ProcessingJob>(`/api/projects/${projectId}/jobs/${jobId}`),
  listPhotos: (projectId: string) => request<Photo[]>(`/api/projects/${projectId}/photos`),
  updatePhoto: (projectId: string, photoId: string, patch: PhotoPatch) =>
    request<Photo>(`/api/projects/${projectId}/photos/${photoId}`, { method: "PATCH", body: JSON.stringify(patch) }),
  batchUpdatePhotos: (projectId: string, photoIds: string[], patch: PhotoPatch) =>
    request<Photo[]>(`/api/projects/${projectId}/photos/batch`, {
      method: "PATCH",
      body: JSON.stringify({ photo_ids: photoIds, ...patch }),
    }),
  listGroups: (projectId: string) => request<PhotoGroup[]>(`/api/projects/${projectId}/groups`),
  listExports: (projectId: string) => request<ExportRecord[]>(`/api/projects/${projectId}/export`),
  exportSelection: (projectId: string, mode: "csv" | "folder" | "zip", statuses: string[]) =>
    request<ExportRecord>(`/api/projects/${projectId}/export`, {
      method: "POST",
      body: JSON.stringify({ mode, statuses }),
    }),
};

export function exportDownloadUrl(projectId: string, exportId: string): string {
  return `${API_BASE}/api/projects/${projectId}/export/${exportId}/download`;
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
