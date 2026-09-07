import { useEffect, useSyncExternalStore } from "react";
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
import { resolveApiBase } from "../../../web/src/lib/apiBase.ts";

export const DESKTOP_QA_IMPORT_BATCH_SIZE = IMPORT_UPLOAD_BATCH_SIZE;
export const DESKTOP_QA_IMPORT_TIMEOUT_MS = 25 * 60 * 1000;
export const DESKTOP_QA_PROCESS_TIMEOUT_MS = 10 * 60 * 1000;
export const DESKTOP_QA_PREVIEW_TIMEOUT_MS = 60 * 1000;

export type DesktopQaConfig = {
  photos: string;
  project: string;
};

export type DesktopQaBootstrap = {
  photos: string;
  project: string;
  evidence?: string;
  api_base: string;
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
  __FRAMEPILOT_API_BASE__?: unknown;
  __FRAMEPILOT_DESKTOP_QA_STARTED__?: unknown;
  __FRAMEPILOT_DESKTOP_QA_NAVIGATE__?: ((href: string) => void) | null;
  __FRAMEPILOT_DESKTOP_QA_MOUNT_CULL__?: ((projectId: string) => void) | null;
  __FRAMEPILOT_DESKTOP_QA_MOUNTED__?: boolean;
  __FRAMEPILOT_DESKTOP_QA_CULL_MOUNTED__?: boolean;
  __FRAMEPILOT_DESKTOP_QA_ROUTE__?: string;
  __FRAMEPILOT_DESKTOP_QA_CULL_HREF__?: string;
  __FRAMEPILOT_DESKTOP_QA_SET_CULL_PROJECT_ID__?: ((projectId: string | null) => void) | null;
  location?: { pathname: string; hash: string };
  dispatchEvent?: (event: Event) => boolean;
  addEventListener?: (type: string, listener: (event: Event) => void) => void;
  removeEventListener?: (type: string, listener: (event: Event) => void) => void;
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

export function parseDesktopQaBootstrap(value: unknown): DesktopQaBootstrap | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const record = value as {
    photos?: unknown;
    project?: unknown;
    evidence?: unknown;
    api_base?: unknown;
  };
  const photos = typeof record.photos === "string" ? record.photos.trim() : "";
  const project = typeof record.project === "string" ? record.project.trim() : "";
  const evidence = typeof record.evidence === "string" ? record.evidence.trim() : "";
  const apiBase = typeof record.api_base === "string" ? record.api_base.trim() : "";
  if (!photos || !project || !apiBase) {
    return null;
  }
  return { photos, project, evidence, api_base: apiBase };
}

export function applyDesktopQaBootstrap(
  win: QaWindow | undefined,
  boot: DesktopQaBootstrap | null | undefined,
): boolean {
  if (!win || !boot) {
    return false;
  }
  if (win.__FRAMEPILOT_WINDOW__ === "preview") {
    return false;
  }
  win.__FRAMEPILOT_DESKTOP__ = true;
  win.__FRAMEPILOT_WINDOW__ = "main";
  win.__FRAMEPILOT_API_BASE__ = boot.api_base;
  win.__FRAMEPILOT_DESKTOP_QA__ = {
    photos: boot.photos,
    project: boot.project,
    evidence: boot.evidence,
  };
  return true;
}

export function spaFlagsLine(now: string, win: QaWindow | undefined, bootstrapped: boolean): string {
  const qa = win?.__FRAMEPILOT_DESKTOP_QA__;
  const apiBase = win?.__FRAMEPILOT_API_BASE__;
  return JSON.stringify({
    milestone: "spa_flags",
    t: now,
    desktop: win?.__FRAMEPILOT_DESKTOP__ === true,
    window_label: typeof win?.__FRAMEPILOT_WINDOW__ === "string" ? win.__FRAMEPILOT_WINDOW__ : "",
    qa: Boolean(qa && typeof qa === "object"),
    api_base: typeof apiBase === "string" && apiBase.trim() !== "",
    resolved_base: resolveApiBase(),
    bootstrapped,
  });
}

export async function withTimeout<T>(promise: Promise<T>, ms: number, message: string): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      promise,
      new Promise<never>((_, reject) => {
        timer = setTimeout(() => reject(new Error(message)), ms);
      }),
    ]);
  } finally {
    if (timer !== undefined) {
      clearTimeout(timer);
    }
  }
}

let desktopQaNavigate: ((href: string) => void) | null = null;
let desktopQaMountCull: ((projectId: string) => void) | null = null;
let desktopQaCullHref = "";
const desktopQaCullListeners = new Set<() => void>();

export const DESKTOP_QA_CULL_HREF_EVENT = "framepilot-qa-cull-href";

export function parseCullProjectId(href: string): string | null {
  const match = /\/projects\/([^/]+)\/cull\/?$/.exec(href);
  const id = match?.[1]?.trim() ?? "";
  return id || null;
}

export function getDesktopQaCullHref(): string {
  const fromWindow = defaultWindow()?.__FRAMEPILOT_DESKTOP_QA_CULL_HREF__;
  if (typeof fromWindow === "string") {
    return fromWindow;
  }
  return desktopQaCullHref;
}

export function subscribeDesktopQaCull(onStoreChange: () => void): () => void {
  desktopQaCullListeners.add(onStoreChange);
  const win = defaultWindow();
  let timer: ReturnType<typeof setInterval> | undefined;
  if (win && typeof win.addEventListener === "function") {
    win.addEventListener(DESKTOP_QA_CULL_HREF_EVENT, onStoreChange);
    timer = setInterval(onStoreChange, 100);
    return () => {
      desktopQaCullListeners.delete(onStoreChange);
      win.removeEventListener?.(DESKTOP_QA_CULL_HREF_EVENT, onStoreChange);
      if (timer !== undefined) {
        clearInterval(timer);
      }
    };
  }
  return () => {
    desktopQaCullListeners.delete(onStoreChange);
  };
}

export function setDesktopQaCullHref(href: string): void {
  desktopQaCullHref = href;
  const win = defaultWindow();
  const projectId = parseCullProjectId(href);
  if (win) {
    win.__FRAMEPILOT_DESKTOP_QA_CULL_HREF__ = href;
    const setter = win.__FRAMEPILOT_DESKTOP_QA_SET_CULL_PROJECT_ID__;
    if (projectId && typeof setter === "function") {
      setter(projectId);
    }
    if (typeof win.dispatchEvent === "function") {
      win.dispatchEvent(
        typeof Event === "function"
          ? new Event(DESKTOP_QA_CULL_HREF_EVENT)
          : ({ type: DESKTOP_QA_CULL_HREF_EVENT } as Event),
      );
    }
  }
  for (const listener of desktopQaCullListeners) {
    listener();
  }
}

export function useDesktopQaCullProjectId(): string | null {
  const href = useSyncExternalStore(subscribeDesktopQaCull, getDesktopQaCullHref, getDesktopQaCullHref);
  return parseCullProjectId(href);
}

export function setDesktopQaNavigate(push: ((href: string) => void) | null): void {
  desktopQaNavigate = push;
  const win = defaultWindow();
  if (win) {
    win.__FRAMEPILOT_DESKTOP_QA_NAVIGATE__ = push;
  }
}

export function setDesktopQaMountCull(mount: ((projectId: string) => void) | null): void {
  desktopQaMountCull = mount;
  const win = defaultWindow();
  if (win) {
    win.__FRAMEPILOT_DESKTOP_QA_MOUNT_CULL__ = mount;
    win.__FRAMEPILOT_DESKTOP_QA_SET_CULL_PROJECT_ID__ = mount
      ? (id) => {
          if (id) {
            mount(id);
          }
        }
      : null;
  }
}

function readDesktopQaMountCull(): ((projectId: string) => void) | null {
  if (desktopQaMountCull) {
    return desktopQaMountCull;
  }
  const fromWindow = defaultWindow()?.__FRAMEPILOT_DESKTOP_QA_MOUNT_CULL__;
  return typeof fromWindow === "function" ? fromWindow : null;
}

export function writeCullWorkspaceMounted(projectId: string): void {
  const win = defaultWindow();
  if (win && win.__FRAMEPILOT_DESKTOP_QA_CULL_MOUNTED__ === true) {
    return;
  }
  if (win) {
    win.__FRAMEPILOT_DESKTOP_QA_CULL_MOUNTED__ = true;
  }
  void invoke("qa_write_evidence", {
    line: JSON.stringify({
      milestone: "cull_workspace",
      t: new Date().toISOString(),
      project_id: projectId,
    }),
  }).catch(() => undefined);
}

export function setDesktopQaRoute(pathname: string): void {
  const win = defaultWindow();
  if (win) {
    win.__FRAMEPILOT_DESKTOP_QA_ROUTE__ = pathname;
  }
}

export function readDesktopQaRoute(): string {
  const route = defaultWindow()?.__FRAMEPILOT_DESKTOP_QA_ROUTE__;
  return typeof route === "string" ? route : "";
}

export function routeShowsCull(href: string, route = readDesktopQaRoute()): boolean {
  return route.includes("/cull") || (href !== "" && route.endsWith(href));
}

function readDesktopQaNavigate(): ((href: string) => void) | null {
  if (desktopQaNavigate) {
    return desktopQaNavigate;
  }
  const fromWindow = defaultWindow()?.__FRAMEPILOT_DESKTOP_QA_NAVIGATE__;
  return typeof fromWindow === "function" ? fromWindow : null;
}

export function cullLocationFields(
  loc: { pathname?: string; hash?: string } | undefined = typeof window === "undefined" ? undefined : window.location,
): { pathname: string; hash: string } {
  return {
    pathname: typeof loc?.pathname === "string" ? loc.pathname : "",
    hash: typeof loc?.hash === "string" ? loc.hash : "",
  };
}

export function locationShowsCull(
  href: string,
  loc: { pathname?: string; hash?: string } | undefined = typeof window === "undefined" ? undefined : window.location,
): boolean {
  const { pathname, hash } = cullLocationFields(loc);
  return pathname.includes("/cull") || hash.includes("/cull") || pathname.endsWith(href) || hash.includes(href);
}

export function hashPush(href: string): void {
  if (typeof window === "undefined" || !window.location) {
    return;
  }
  const hash = href.startsWith("#") ? href : `#${href}`;
  if (window.location.hash === hash) {
    if (typeof window.dispatchEvent === "function") {
      window.dispatchEvent(typeof Event === "function" ? new Event("hashchange") : ({ type: "hashchange" } as Event));
    }
    return;
  }
  window.location.hash = hash;
}

export function historyPush(href: string): void {
  const push = readDesktopQaNavigate();
  if (push) {
    push(href);
    return;
  }
  hashPush(href);
}

async function waitForCullPush(
  fallback: (href: string) => void,
  href: string,
  sleep: (ms: number) => Promise<void>,
): Promise<"mount" | "store" | "react" | "history"> {
  const projectId = parseCullProjectId(href);
  let mounted = false;
  if (projectId) {
    setDesktopQaCullHref(href);
    const mount = readDesktopQaMountCull();
    if (mount) {
      mount(projectId);
      mounted = true;
    }
  }
  const push = readDesktopQaNavigate();
  if (push) {
    push(href);
    if (
      typeof window !== "undefined" &&
      typeof CustomEvent === "function" &&
      typeof window.dispatchEvent === "function"
    ) {
      window.dispatchEvent(new CustomEvent("framepilot-qa-navigate", { detail: href }));
    }
  } else {
    fallback(href);
  }
  await sleep(0);
  if (mounted) {
    return "mount";
  }
  if (parseCullProjectId(getDesktopQaCullHref())) {
    return "store";
  }
  if (push) {
    return "react";
  }
  return "history";
}

export type StartDesktopQaOptions = {
  win?: QaWindow;
  api?: DesktopQaApi;
  writeEvidence?: (line: string) => Promise<unknown>;
  push: (href: string) => void;
  queryPreviewImages?: RunDesktopQaOptions["queryPreviewImages"];
  now?: () => string;
  sleep?: (ms: number) => Promise<void>;
  signal?: AbortSignal;
  readBootstrap?: () => Promise<unknown>;
};

function defaultWindow(): QaWindow | undefined {
  return typeof window === "undefined" ? undefined : window;
}

export async function startDesktopQaFromWindow(options: StartDesktopQaOptions): Promise<boolean> {
  const win = options.win ?? defaultWindow();
  if (!win || win.__FRAMEPILOT_WINDOW__ === "preview") {
    return false;
  }
  if (win.__FRAMEPILOT_DESKTOP_QA_STARTED__ === true) {
    return false;
  }
  let config = readDesktopQaConfig(win);
  if (!config) {
    try {
      const raw = await (options.readBootstrap ?? (() => invoke("qa_bootstrap")))();
      applyDesktopQaBootstrap(win, parseDesktopQaBootstrap(raw));
      config = readDesktopQaConfig(win);
    } catch {
      config = readDesktopQaConfig(win);
    }
  }
  if (!config) {
    return false;
  }
  win.__FRAMEPILOT_DESKTOP_QA_STARTED__ = true;
  const writeEvidence = options.writeEvidence ?? ((line: string) => invoke("qa_write_evidence", { line }));
  const now = options.now ?? (() => new Date().toISOString());
  await writeEvidence(JSON.stringify({ milestone: "qa_started", t: now(), resolved_base: resolveApiBase() })).catch(
    () => undefined,
  );
  const api = options.api ?? {
    ...productionApi,
    getHealth: () => withTimeout(productionApi.getHealth(), 15_000, "GET /api/health timed out after 15s"),
    getSettings: () => withTimeout(productionApi.getSettings(), 15_000, "GET /api/settings timed out after 15s"),
  };
  try {
    await runDesktopQa({
      api,
      writeEvidence,
      push: options.push,
      queryPreviewImages:
        options.queryPreviewImages ??
        (() => (typeof document === "undefined" ? [] : Array.from(document.querySelectorAll("img")))),
      config,
      now,
      sleep: options.sleep,
      signal: options.signal,
    });
  } catch (error: unknown) {
    if (!options.signal?.aborted) {
      console.error("FramePilot desktop QA runner failed", error);
      await writeEvidence(qaFailLine(new Date().toISOString(), error)).catch(() => undefined);
    }
  }
  return true;
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
  const images = queryPreviewImages();
  const previewCount = images.filter((image) => `${image.currentSrc || image.src || ""}`.includes("/previews/")).length;
  throw new Error(
    `culling preview img did not reach naturalWidth > 0 (imgs=${images.length}, previews=${previewCount})`,
  );
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
    throw new Error(`accepted_files ${importResult.accepted_files} does not match count ${expected}`);
  }
  await writeMilestone(options.writeEvidence, "import_complete", now, {
    accepted_files: importResult.accepted_files,
  });

  const processJob = await api.processProject(project.id);
  if (processJob.id && processJob.status !== "complete") {
    await waitForJob(api, project.id, processJob.id, processTimeoutMs, sleep, options.signal);
  }
  await writeMilestone(options.writeEvidence, "process_complete", now);

  const cullHref = `/projects/${project.id}/cull`;
  const via = await waitForCullPush(options.push, cullHref, sleep);
  const loc = cullLocationFields();
  await writeMilestone(options.writeEvidence, "cull_push", now, {
    href: cullHref,
    via,
    cull_project_id: parseCullProjectId(getDesktopQaCullHref()),
    route: readDesktopQaRoute(),
    pathname: loc.pathname,
    hash: loc.hash,
  });
  const naturalWidth = await waitForPreview(options.queryPreviewImages, previewTimeoutMs, sleep, options.signal);
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
  setDesktopQaNavigate((href) => navigate(href));
  const win = defaultWindow();
  if (win && win.__FRAMEPILOT_DESKTOP_QA_MOUNTED__ !== true) {
    win.__FRAMEPILOT_DESKTOP_QA_MOUNTED__ = true;
    void invoke("qa_write_evidence", {
      line: JSON.stringify({ milestone: "qa_runner_mounted", t: new Date().toISOString() }),
    }).catch(() => undefined);
  }
  useEffect(() => {
    setDesktopQaNavigate((href) => navigate(href));
    void startDesktopQaFromWindow({
      push: (href) => navigate(href),
    });
    return () => {
      if (defaultWindow()?.__FRAMEPILOT_DESKTOP_QA_STARTED__ !== true) {
        setDesktopQaNavigate(null);
      }
    };
  }, [navigate]);
  return null;
}
