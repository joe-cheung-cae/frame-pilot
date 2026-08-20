import { getCurrentWebview } from "@tauri-apps/api/webview";
import { open } from "@tauri-apps/plugin-dialog";
import { revealItemInDir } from "@tauri-apps/plugin-opener";
import type { NativeDragDropEvent } from "@/lib/droppedPaths";

export type NativeFs = {
  pickDirectory: () => Promise<string | null>;
  pickImageFiles: () => Promise<string[] | null>;
  revealInFileManager: (targetPath: string) => Promise<void>;
  subscribeDragDrop: (handler: (event: NativeDragDropEvent) => void) => Promise<() => void>;
};

const IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"];

function asDirectoryPath(selected: unknown): string | null {
  return typeof selected === "string" && selected.length > 0 ? selected : null;
}

function asFilePaths(selected: unknown): string[] | null {
  if (selected == null) {
    return null;
  }
  if (typeof selected === "string") {
    return selected.length > 0 ? [selected] : null;
  }
  if (Array.isArray(selected)) {
    return selected.filter((item): item is string => typeof item === "string" && item.length > 0);
  }
  return null;
}

async function pickDirectory(): Promise<string | null> {
  const selected = await open({ directory: true, multiple: false });
  return asDirectoryPath(selected);
}

async function pickImageFiles(): Promise<string[] | null> {
  const selected = await open({
    multiple: true,
    filters: [{ name: "Images", extensions: IMAGE_EXTENSIONS }],
  });
  return asFilePaths(selected);
}

async function revealInFileManager(targetPath: string): Promise<void> {
  await revealItemInDir(targetPath);
}

async function subscribeDragDrop(handler: (event: NativeDragDropEvent) => void): Promise<() => void> {
  return getCurrentWebview().onDragDropEvent((event) => {
    const payload = event.payload;
    if (payload.type === "enter") {
      handler({ type: "enter", paths: payload.paths });
      return;
    }
    if (payload.type === "over") {
      handler({ type: "over" });
      return;
    }
    if (payload.type === "drop") {
      handler({ type: "drop", paths: payload.paths });
      return;
    }
    handler({ type: "leave" });
  });
}

const nativeFs: NativeFs = {
  pickDirectory,
  pickImageFiles,
  revealInFileManager,
  subscribeDragDrop,
};

export function getNativeFs(): NativeFs | null {
  return nativeFs;
}
