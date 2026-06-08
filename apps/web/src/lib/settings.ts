import { EXPORT_STATUSES, type ExportStatus } from "./exportSelection.ts";

type StatusStorage = Pick<Storage, "getItem" | "setItem">;
type SaveExportStatusPreferenceResult = {
  saved: boolean;
  statuses: ExportStatus[];
};

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
  return saveExportStatusPreferenceResult(statuses, storage).statuses;
}

function saveExportStatusPreferenceResult(
  statuses: readonly ExportStatus[],
  storage = browserStorage(),
): SaveExportStatusPreferenceResult {
  const normalized = normalizeExportStatusPreference(statuses);
  if (!storage) {
    return { saved: false, statuses: normalized };
  }

  try {
    storage.setItem(EXPORT_STATUS_PREFERENCE_KEY, JSON.stringify(normalized));
    return { saved: true, statuses: normalized };
  } catch {
    return { saved: false, statuses: normalized };
  }
}

export function toggleExportStatusPreference(
  current: readonly ExportStatus[],
  status: ExportStatus,
  storage = browserStorage(),
): ExportStatus[] {
  const next = current.includes(status) ? current.filter((item) => item !== status) : [...current, status];
  return next.length ? saveExportStatusPreference(next, storage) : next;
}

export function isOnlySelectedExportStatus(current: readonly ExportStatus[], status: ExportStatus): boolean {
  return current.length === 1 && current.includes(status);
}

export function toggleSavedExportStatusPreference(
  current: readonly ExportStatus[],
  status: ExportStatus,
  storage = browserStorage(),
): { message: string; statuses: ExportStatus[] } {
  if (isOnlySelectedExportStatus(current, status)) {
    return { message: "Keep at least one default export status.", statuses: [...current] };
  }

  const next = current.includes(status) ? current.filter((item) => item !== status) : [...current, status];
  const result = saveExportStatusPreferenceResult(next, storage);
  return {
    message: result.saved ? "Saved locally." : "Preference changed for this session. Browser storage did not save it.",
    statuses: result.statuses,
  };
}
