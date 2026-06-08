type ProjectCreateDraft = {
  isCreating: boolean;
  name: string;
  rootPath: string;
};

export type NormalizedProjectCreateDraft = {
  projectName: string;
  projectRootPath?: string;
};

export function projectCreateActionBlockMessage({
  isCreating,
  name,
}: Pick<ProjectCreateDraft, "isCreating" | "name">): string {
  if (isCreating) {
    return "Project creation is already running.";
  }

  if (!name.trim()) {
    return "Enter a project name before creating a project.";
  }

  return "";
}

export function normalizeProjectCreateDraft({
  name,
  rootPath,
}: Pick<ProjectCreateDraft, "name" | "rootPath">): NormalizedProjectCreateDraft {
  const projectName = name.trim();
  const projectRootPath = rootPath.trim();
  return projectRootPath ? { projectName, projectRootPath } : { projectName };
}

export function projectDataFolderHint(rootPath: string): string {
  return rootPath.trim()
    ? "FramePilot will create copied originals, previews, caches, and exports in this local project folder."
    : "FramePilot will use its managed local data folder for copied originals, previews, caches, and exports.";
}

export function projectCreationRecoveryHint(rootPath: string): string {
  return rootPath.trim()
    ? "Check that the local project data folder exists and is writable, or leave it blank to use FramePilot's managed local data folder."
    : "Confirm the local FramePilot API is running, then try creating the project again.";
}
