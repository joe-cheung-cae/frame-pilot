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

export const NONEMPTY_PROJECT_ROOT_CONFIRM =
  "This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?";

export const NONEMPTY_PROJECT_ROOT_API_DETAIL =
  "Project root path is not empty; pass acknowledge_nonempty=true to use it anyway";

export function isNonemptyProjectRootError(error: unknown): boolean {
  return error instanceof Error && error.message === NONEMPTY_PROJECT_ROOT_API_DETAIL;
}

export async function createProjectWithNonemptyConfirm<T>(
  draft: NormalizedProjectCreateDraft,
  options: {
    createProject: (name: string, rootPath?: string, createOptions?: { acknowledgeNonempty?: boolean }) => Promise<T>;
    confirmNonempty: (message: string) => boolean | Promise<boolean>;
  },
): Promise<T> {
  try {
    return await options.createProject(draft.projectName, draft.projectRootPath);
  } catch (error) {
    if (!isNonemptyProjectRootError(error)) {
      throw error;
    }
    const confirmed = await options.confirmNonempty(NONEMPTY_PROJECT_ROOT_CONFIRM);
    if (!confirmed) {
      throw error;
    }
    return options.createProject(draft.projectName, draft.projectRootPath, { acknowledgeNonempty: true });
  }
}

export async function registerPickedProjectRoot(options: {
  pickDirectory: () => Promise<string | null>;
  registerRoot: (path: string) => Promise<{ path: string }>;
}): Promise<string | null> {
  const picked = await options.pickDirectory();
  if (!picked) {
    return null;
  }
  const registered = await options.registerRoot(picked);
  return registered.path;
}
