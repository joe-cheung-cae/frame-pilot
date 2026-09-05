import type { ReviewShortcutCommand } from "./reviewShortcuts";

export const REVIEW_SYNC_EVENT = "framepilot-review-sync";
export const REVIEW_SYNC_REQUEST_EVENT = "framepilot-review-sync-request";
export const REVIEW_COMMAND_EVENT = "framepilot-review-command";
export const PREVIEW_OPENED_EVENT = "framepilot-preview-opened";
export const PREVIEW_CLOSED_EVENT = "framepilot-preview-closed";

export type DetachedPreviewToggleResult =
  | { ok: true; open: boolean }
  | { ok: false; reason: string };

export type ReviewSyncCompareItem = {
  photoId: string;
  filename: string;
  previewPath: string | null;
};

export type ReviewSyncPayload = {
  projectId: string;
  activePhotoId: string | null;
  activeGroupId: string | null;
  filename: string | null;
  previewPath: string | null;
  compareMode: boolean;
  compare: ReviewSyncCompareItem[];
  previewZoom: number;
};

export type ReviewSyncInput = {
  projectId?: unknown;
  activePhotoId?: unknown;
  activeGroupId?: unknown;
  filename?: unknown;
  previewPath?: unknown;
  preview_path?: unknown;
  compareMode?: unknown;
  compare?: unknown;
  previewZoom?: unknown;
  originalPath?: unknown;
  original_path?: unknown;
  project_copy_path?: unknown;
  source_identity?: unknown;
};

function asNonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function sanitizeCompareItem(value: unknown): ReviewSyncCompareItem | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const row = value as {
    photoId?: unknown;
    filename?: unknown;
    previewPath?: unknown;
    preview_path?: unknown;
  };
  const photoId = asNonEmptyString(row.photoId);
  if (!photoId) {
    return null;
  }
  return {
    photoId,
    filename: asNonEmptyString(row.filename) ?? "",
    previewPath: asNonEmptyString(row.previewPath) ?? asNonEmptyString(row.preview_path),
  };
}

export function toReviewSyncPayload(input: ReviewSyncInput): ReviewSyncPayload {
  const compareIn = Array.isArray(input.compare) ? input.compare : [];
  return {
    projectId: asNonEmptyString(input.projectId) ?? "",
    activePhotoId: asNonEmptyString(input.activePhotoId),
    activeGroupId: asNonEmptyString(input.activeGroupId),
    filename: asNonEmptyString(input.filename),
    previewPath: asNonEmptyString(input.previewPath) ?? asNonEmptyString(input.preview_path),
    compareMode: input.compareMode === true,
    compare: compareIn
      .map((item) => sanitizeCompareItem(item))
      .filter((item): item is ReviewSyncCompareItem => item !== null),
    previewZoom:
      typeof input.previewZoom === "number" && Number.isFinite(input.previewZoom) ? input.previewZoom : 1,
  };
}

type FramepilotWindow = {
  __FRAMEPILOT_WINDOW__?: unknown;
};

function readWindow(): FramepilotWindow | undefined {
  return (globalThis as { window?: FramepilotWindow }).window;
}

export function framepilotWindowLabel(): "main" | "preview" | null {
  const label = readWindow()?.__FRAMEPILOT_WINDOW__;
  if (label === "preview") {
    return "preview";
  }
  if (label === "main") {
    return "main";
  }
  return null;
}

export function isPreviewWindow(): boolean {
  return framepilotWindowLabel() === "preview";
}

export function shouldApplyReviewSync(): boolean {
  return isPreviewWindow();
}

export function shouldApplyReviewCommand(): boolean {
  return !isPreviewWindow();
}

export async function requestDetachedPreviewToggle(): Promise<DetachedPreviewToggleResult> {
  return { ok: false, reason: "not-desktop" };
}

export async function requestDetachedPreviewClose(): Promise<DetachedPreviewToggleResult> {
  return { ok: true, open: false };
}

export async function emitReviewSync(payload: ReviewSyncPayload | ReviewSyncInput): Promise<void> {
  void payload;
}

export async function emitReviewSyncRequest(): Promise<void> {}

export async function emitReviewCommand(command: ReviewShortcutCommand): Promise<void> {
  void command;
}

export async function subscribeReviewSync(
  handler: (payload: ReviewSyncPayload) => void,
): Promise<() => void> {
  void handler;
  return () => {};
}

export async function subscribeReviewSyncRequest(handler: () => void): Promise<() => void> {
  void handler;
  return () => {};
}

export async function subscribeReviewCommand(
  handler: (command: ReviewShortcutCommand) => void,
): Promise<() => void> {
  void handler;
  return () => {};
}

export async function subscribePreviewOpened(handler: () => void): Promise<() => void> {
  void handler;
  return () => {};
}

export async function subscribePreviewClosed(handler: () => void): Promise<() => void> {
  void handler;
  return () => {};
}
