import { open } from "@tauri-apps/plugin-dialog";
import { revealItemInDir } from "@tauri-apps/plugin-opener";

export type NativeFs = {
  pickDirectory: () => Promise<string | null>;
  pickImageFiles: () => Promise<string[] | null>;
  revealInFileManager: (targetPath: string) => Promise<void>;
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

const nativeFs: NativeFs = {
  pickDirectory,
  pickImageFiles,
  revealInFileManager,
};

export function getNativeFs(): NativeFs | null {
  return nativeFs;
}
