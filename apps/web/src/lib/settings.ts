import { EXPORT_STATUSES, type ExportStatus } from "./exportSelection.ts";

type StatusStorage = Pick<Storage, "getItem" | "setItem">;

export const DEFAULT_EXPORT_STATUS_PREFERENCE: ExportStatus[] = ["Pick", "Maybe"];
export const EXPORT_STATUS_PREFERENCE_KEY = "framepilot.defaultExportStatuses";

function browserStorage(): StatusStorage | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.localStorage;
}

export function normalizeExportStatusPreference(value: unknown): ExportStatus[] {
  if (!Array.isArray(value)) {
    return DEFAULT_EXPORT_STATUS_PREFERENCE;
  }
  const selected = EXPORT_STATUSES.filter((status) => value.includes(status));
  return selected.length ? selected : DEFAULT_EXPORT_STATUS_PREFERENCE;
}

export function loadExportStatusPreference(storage = browserStorage()): ExportStatus[] {
  if (!storage) {
    return DEFAULT_EXPORT_STATUS_PREFERENCE;
  }
  try {
    const raw = storage.getItem(EXPORT_STATUS_PREFERENCE_KEY);
    return raw ? normalizeExportStatusPreference(JSON.parse(raw)) : DEFAULT_EXPORT_STATUS_PREFERENCE;
  } catch {
    return DEFAULT_EXPORT_STATUS_PREFERENCE;
  }
}

export function saveExportStatusPreference(
  statuses: readonly ExportStatus[],
  storage = browserStorage(),
): ExportStatus[] {
  const normalized = normalizeExportStatusPreference(statuses);
  if (storage) {
    storage.setItem(EXPORT_STATUS_PREFERENCE_KEY, JSON.stringify(normalized));
  }
  return normalized;
}

export function toggleExportStatusPreference(
  current: readonly ExportStatus[],
  status: ExportStatus,
  storage = browserStorage(),
): ExportStatus[] {
  const next = current.includes(status) ? current.filter((item) => item !== status) : [...current, status];
  return next.length ? saveExportStatusPreference(next, storage) : next;
}
