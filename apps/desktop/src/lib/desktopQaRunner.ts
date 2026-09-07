import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { invoke } from "@tauri-apps/api/core";
import {
  api as productionApi,
  IMPORT_UPLOAD_BATCH_SIZE,
  type AppSettings,
  type HealthStatus,
  type ImportResult,
  type ProcessingJob,
  type Project,
} from "../../../web/src/lib/api.ts";

export const DESKTOP_QA_IMPORT_BATCH_SIZE = IMPORT_UPLOAD_BATCH_SIZE;
export const DESKTOP_QA_IMPORT_TIMEOUT_MS = 25 * 60 * 1000;
export const DESKTOP_QA_PROCESS_TIMEOUT_MS = 10 * 60 * 1000;
export const DESKTOP_QA_PREVIEW_TIMEOUT_MS = 60 * 1000;

export type DesktopQaConfig = {
  photos: string;
  project: string;
};

export type DesktopQaApi = {
  getHealth: () => Promise<HealthStatus>;
  getSettings: () => Promise<AppSettings>;
  registerDesktopProjectRoot: (path: string) => Promise<{ path: string }>;
  createProject: (name: string, rootPath?: string) => Promise<Pick<Project, "id">>;
  importPhotosFromPaths: (
    projectId: string,
    paths: readonly string[],
  ) => Promise<Pick<ImportResult, "accepted_files" | "skipped_files" | "expanded_total" | "job">>;
  processProject: (projectId: string) => Promise<Pick<ProcessingJob, "id" | "status" | "error_message">>;
  getJob: (
    projectId: string,
    jobId: string,
  ) => Promise<Pick<ProcessingJob, "id" | "status" | "job_type" | "error_message">>;
};

export type RunDesktopQaOptions = {
  api: DesktopQaApi;
  writeEvidence: (line: string) => Promise<unknown>;
  push: (href: string) => void;
  queryPreviewImages: () => Array<Pick<HTMLImageElement, "src" | "currentSrc" | "complete" | "naturalWidth">>;
  config: DesktopQaConfig;
  now?: () => string;
  sleep?: (ms: number) => Promise<void>;
  signal?: AbortSignal;
  importTimeoutMs?: number;
  processTimeoutMs?: number;
  previewTimeoutMs?: number;
};

type QaWindow = {
  __FRAMEPILOT_DESKTOP__?: unknown;
  __FRAMEPILOT_WINDOW__?: unknown;
  __FRAMEPILOT_DESKTOP_QA__?: unknown;
};

function defaultSleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function throwIfAborted(signal?: AbortSignal): void {
  if (signal?.aborted) {
    throw new Error("desktop QA runner aborted");
  }
}

export function qaFailLine(now: string, error: unknown): string {
  const message = error instanceof Error ? error.message : String(error ?? "desktop QA runner failed");
  return JSON.stringify({
    milestone: "fail",
    t: now,
    fail_reason: message.slice(0, 500),
  });
}

export function readDesktopQaConfig(win: QaWindow | undefined): DesktopQaConfig | null {
  if (!win || win.__FRAMEPILOT_DESKTOP__ !== true || win.__FRAMEPILOT_WINDOW__ !== "main") {
    return null;
  }
  const qa = win.__FRAMEPILOT_DESKTOP_QA__;
  if (!qa || typeof qa !== "object") {
    return null;
  }
  const record = qa as { photos?: unknown; project?: unknown };
  const photos = typeof record.photos === "string" ? record.photos.trim() : "";
  const project = typeof record.project === "string" ? record.project.trim() : "";
  if (!photos || !project) {
    return null;
  }
  return { photos, project };
}

async function writeMilestone(
  writeEvidence: (line: string) => Promise<unknown>,
  milestone: string,
  now: () => string,
  extra: Record<string, unknown> = {},
): Promise<void> {
  await writeEvidence(JSON.stringify({ milestone, t: now(), ...extra }));
}

function jobIsTerminalFailure(status: string): boolean {
  return status === "failed" || status === "cancelled" || status === "complete_with_errors";
}

async function waitForJob(
  api: DesktopQaApi,
  projectId: string,
  jobId: string,
  timeoutMs: number,
  sleep: (ms: number) => Promise<void>,
  signal?: AbortSignal,
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    throwIfAborted(signal);
    const job = await api.getJob(projectId, jobId);
    if (job.status === "complete") {
      return;
    }
    if (jobIsTerminalFailure(job.status)) {
      throw new Error(job.error_message || `job ${job.job_type ?? jobId} ${job.status}`);
    }
    await sleep(500);
  }
  throw new Error(`job ${jobId} timed out`);
}

async function waitForPreview(
  queryPreviewImages: RunDesktopQaOptions["queryPreviewImages"],
  timeoutMs: number,
  sleep: (ms: number) => Promise<void>,
  signal?: AbortSignal,
): Promise<number> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    throwIfAborted(signal);
    for (const image of queryPreviewImages()) {
      const src = `${image.currentSrc || image.src || ""}`;
      if (src.includes("/previews/") && image.complete && image.naturalWidth > 0) {
        return image.naturalWidth;
      }
    }
    await sleep(250);
  }
  throw new Error("culling preview img did not reach naturalWidth > 0");
}

export async function runDesktopQa(options: RunDesktopQaOptions): Promise<void> {
  const api = options.api;
  const sleep = options.sleep ?? defaultSleep;
  const now = options.now ?? (() => new Date().toISOString());
  const importTimeoutMs = options.importTimeoutMs ?? DESKTOP_QA_IMPORT_TIMEOUT_MS;
  const processTimeoutMs = options.processTimeoutMs ?? DESKTOP_QA_PROCESS_TIMEOUT_MS;
  const previewTimeoutMs = options.previewTimeoutMs ?? DESKTOP_QA_PREVIEW_TIMEOUT_MS;

  if (DESKTOP_QA_IMPORT_BATCH_SIZE < 1) {
    throw new Error("IMPORT_UPLOAD_BATCH_SIZE must be a positive integer");
  }
  throwIfAborted(options.signal);
  await api.getHealth();
  const settings = await api.getSettings();
  const importWorkers =
    Number.isFinite(settings.import_workers) && settings.import_workers > 0 ? settings.import_workers : 1;
  await writeMilestone(options.writeEvidence, "idle", now, { import_workers: importWorkers });

  await api.registerDesktopProjectRoot(options.config.project);
  const project = await api.createProject("desktop-500-gui", options.config.project);

  const importResult = await api.importPhotosFromPaths(project.id, [options.config.photos]);
  if (importResult.job?.id) {
    await waitForJob(api, project.id, importResult.job.id, importTimeoutMs, sleep, options.signal);
  }
  const skipped = importResult.skipped_files ?? 0;
  if (skipped !== 0) {
    throw new Error(`import skipped ${skipped} files; JPEG-only corpus must skip 0`);
  }
  const expected = importResult.expanded_total ?? importResult.accepted_files;
  if (importResult.accepted_files !== expected) {
    throw new Error(
      `accepted_files ${importResult.accepted_files} does not match count ${expected}`,
    );
  }
  await writeMilestone(options.writeEvidence, "import_complete", now, {
    accepted_files: importResult.accepted_files,
  });

  const processJob = await api.processProject(project.id);
  if (processJob.id && processJob.status !== "complete") {
    await waitForJob(api, project.id, processJob.id, processTimeoutMs, sleep, options.signal);
  }
  await writeMilestone(options.writeEvidence, "process_complete", now);

  options.push(`/projects/${project.id}/cull`);
  const naturalWidth = await waitForPreview(
    options.queryPreviewImages,
    previewTimeoutMs,
    sleep,
    options.signal,
  );
  await writeMilestone(options.writeEvidence, "first_preview", now, {
    preview_natural_width: naturalWidth,
  });
  await writeMilestone(options.writeEvidence, "done", now, {
    accepted_files: importResult.accepted_files,
    preview_natural_width: naturalWidth,
  });
}

export function DesktopQaRunner() {
  const navigate = useNavigate();
  useEffect(() => {
    const config = readDesktopQaConfig(typeof window === "undefined" ? undefined : window);
    if (!config) {
      return;
    }
    const controller = new AbortController();
    void runDesktopQa({
      api: productionApi,
      writeEvidence: (line) => invoke("qa_write_evidence", { line }),
      push: (href) => navigate(href),
      queryPreviewImages: () => Array.from(document.querySelectorAll("img")),
      config,
      signal: controller.signal,
    }).catch((error: unknown) => {
      if (controller.signal.aborted) {
        return;
      }
      console.error("FramePilot desktop QA runner failed", error);
      void invoke("qa_write_evidence", { line: qaFailLine(new Date().toISOString(), error) }).catch(
        () => undefined,
      );
    });
    return () => controller.abort();
  }, [navigate]);
  return null;
}
