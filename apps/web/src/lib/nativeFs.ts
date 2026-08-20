export type NativeFs = {
  pickDirectory: () => Promise<string | null>;
  pickImageFiles: () => Promise<string[] | null>;
  revealInFileManager: (targetPath: string) => Promise<void>;
};

export function getNativeFs(): NativeFs | null {
  return null;
}
