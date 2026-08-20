export type DroppedPathFile = {
  path?: string | null;
  name?: string;
};

export type DroppedPathDataTransferItem = {
  kind?: string;
  getAsFile?: () => DroppedPathFile | null;
};

export type DroppedPathDataTransfer = {
  files?: ArrayLike<DroppedPathFile> | null;
  items?: ArrayLike<DroppedPathDataTransferItem> | null;
  types?: ArrayLike<string> | null;
  getData?: (format: string) => string;
};

export type DroppedPathEvent = {
  dataTransfer?: DroppedPathDataTransfer | null;
};

export type NativeDragDropEvent =
  | { type: "enter"; paths: string[] }
  | { type: "over" }
  | { type: "drop"; paths: string[] }
  | { type: "leave" };

function pushUnique(paths: string[], value: string): void {
  if (!value || paths.includes(value)) {
    return;
  }
  paths.push(value);
}

function pathFromFileUrl(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed.toLowerCase().startsWith("file:")) {
    return null;
  }
  try {
    const url = new URL(trimmed);
    let pathname = decodeURIComponent(url.pathname);
    if (url.host && url.host !== "localhost") {
      return `\\\\${url.host}${pathname.replace(/\//g, "\\")}`;
    }
    if (/^\/[A-Za-z]:/.test(pathname)) {
      pathname = pathname.slice(1);
    }
    return pathname || null;
  } catch {
    return null;
  }
}

function isAbsoluteFilesystemPath(value: string): boolean {
  if (!value || value.includes("\0")) {
    return false;
  }
  if (value.startsWith("/")) {
    return true;
  }
  if (/^[A-Za-z]:[\\/]/.test(value)) {
    return true;
  }
  return value.startsWith("\\\\");
}

function collectFromText(text: string, paths: string[]): void {
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }
    const fromUrl = pathFromFileUrl(trimmed);
    if (fromUrl) {
      pushUnique(paths, fromUrl);
      continue;
    }
    if (isAbsoluteFilesystemPath(trimmed)) {
      pushUnique(paths, trimmed);
    }
  }
}

function readTransferData(dataTransfer: DroppedPathDataTransfer, format: string): string {
  if (typeof dataTransfer.getData !== "function") {
    return "";
  }
  try {
    return dataTransfer.getData(format) ?? "";
  } catch {
    return "";
  }
}

export function collectDroppedPaths(event: DroppedPathEvent | null | undefined): string[] {
  const paths: string[] = [];
  const dataTransfer = event?.dataTransfer;
  if (!dataTransfer) {
    return paths;
  }

  const files = dataTransfer.files;
  if (files) {
    for (let index = 0; index < files.length; index += 1) {
      const path = files[index]?.path?.trim() ?? "";
      if (path) {
        pushUnique(paths, path);
      }
    }
  }

  const items = dataTransfer.items;
  if (items) {
    for (let index = 0; index < items.length; index += 1) {
      const item = items[index];
      if (item?.kind !== "file" || typeof item.getAsFile !== "function") {
        continue;
      }
      const path = item.getAsFile()?.path?.trim() ?? "";
      if (path) {
        pushUnique(paths, path);
      }
    }
  }

  const formats = new Set<string>(["text/uri-list", "text/plain", "URL"]);
  if (dataTransfer.types) {
    for (let index = 0; index < dataTransfer.types.length; index += 1) {
      const type = dataTransfer.types[index];
      if (type) {
        formats.add(type);
      }
    }
  }
  for (const format of formats) {
    if (format !== "text/uri-list" && format !== "text/plain" && format !== "URL") {
      continue;
    }
    collectFromText(readTransferData(dataTransfer, format), paths);
  }

  return paths;
}

export function importDropOverlayPointerEvents(dragActive: boolean): "none" | "auto" {
  return dragActive ? "auto" : "none";
}
