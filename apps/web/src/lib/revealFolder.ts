export type RevealFolderKind = "project" | "export";

export type RevealFolderPaths = {
  rootPath?: string | null;
  outputPath?: string | null;
};

export function projectExportRoot(rootPath: string): string {
  return `${rootPath.replace(/[\\/]+$/, "")}/exports`;
}

export function revealFolderTargetPath(kind: RevealFolderKind, paths: RevealFolderPaths): string | null {
  if (kind === "project") {
    const rootPath = paths.rootPath?.trim() ?? "";
    return rootPath || null;
  }

  const outputPath = paths.outputPath?.trim() ?? "";
  if (outputPath) {
    return outputPath;
  }

  const rootPath = paths.rootPath?.trim() ?? "";
  return rootPath ? projectExportRoot(rootPath) : null;
}

export async function revealFolder(
  kind: RevealFolderKind,
  paths: RevealFolderPaths,
  revealInFileManager: ((targetPath: string) => Promise<void>) | null | undefined,
): Promise<boolean> {
  const targetPath = revealFolderTargetPath(kind, paths);
  if (!targetPath || !revealInFileManager) {
    return false;
  }
  await revealInFileManager(targetPath);
  return true;
}
