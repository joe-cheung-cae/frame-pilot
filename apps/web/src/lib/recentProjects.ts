type RecentStorage = Pick<Storage, "getItem" | "setItem">;

export const LAST_OPENED_PROJECT_KEY = "framepilot.lastOpenedProjectId";

function browserStorage(): RecentStorage | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.localStorage;
}

export function normalizeLastOpenedProjectId(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed || null;
}

export function loadLastOpenedProjectId(storage = browserStorage()): string | null {
  if (!storage) {
    return null;
  }
  try {
    return normalizeLastOpenedProjectId(storage.getItem(LAST_OPENED_PROJECT_KEY));
  } catch {
    return null;
  }
}

export function saveLastOpenedProjectId(projectId: string, storage = browserStorage()): string | null {
  const normalized = normalizeLastOpenedProjectId(projectId);
  if (!normalized) {
    return null;
  }
  if (!storage) {
    return normalized;
  }
  try {
    storage.setItem(LAST_OPENED_PROJECT_KEY, normalized);
  } catch {
    return normalized;
  }
  return normalized;
}

export function orderProjectsByLastOpened<T extends { id: string }>(
  projects: readonly T[],
  lastOpenedId: string | null | undefined,
): T[] {
  const lastOpened = normalizeLastOpenedProjectId(lastOpenedId);
  if (!lastOpened) {
    return [...projects];
  }

  const match = projects.find((project) => project.id === lastOpened);
  if (!match) {
    return [...projects];
  }

  return [match, ...projects.filter((project) => project.id !== lastOpened)];
}
