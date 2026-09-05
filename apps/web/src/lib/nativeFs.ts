import type { NativeDragDropEvent } from "./droppedPaths";

export type NativeFs = {
  pickDirectory: () => Promise<string | null>;
  pickImageFiles: () => Promise<string[] | null>;
  revealInFileManager: (targetPath: string) => Promise<void>;
  subscribeDragDrop: (handler: (event: NativeDragDropEvent) => void) => Promise<() => void>;
  applyDataDirectory?: (path: string) => Promise<void>;
};

export function getNativeFs(): NativeFs | null {
  return null;
}
