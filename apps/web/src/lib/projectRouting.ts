import type { Project } from "@/lib/api";

type ActiveImportState = { status?: string } | null | undefined;
type ProjectRouteState = Pick<Project, "id" | "total_images" | "processed_images"> & {
  active_import_job?: ActiveImportState;
};
type ProjectActionState = Pick<Project, "total_images" | "processed_images"> & {
  active_import_job?: ActiveImportState;
};
type ProjectProgressState = Pick<Project, "total_images" | "processed_images"> & {
  active_import_job?: ActiveImportState;
};
export type ProjectWorkflowStep = "import" | "process" | "cull" | "export";

export function projectHasActiveImport(project: { active_import_job?: ActiveImportState }): boolean {
  const status = project.active_import_job?.status;
  return status === "queued" || status === "running";
}

export function projectsHaveActiveImport(projects: readonly { active_import_job?: ActiveImportState }[]): boolean {
  return projects.some((project) => projectHasActiveImport(project));
}

export function projectNextHref(project: ProjectRouteState): string {
  if (projectHasActiveImport(project)) {
    return `/projects/${project.id}/import`;
  }
  if (project.total_images <= 0) {
    return `/projects/${project.id}/import`;
  }
  if (project.processed_images > 0) {
    return `/projects/${project.id}/cull`;
  }
  return `/projects/${project.id}/process`;
}

export function projectNextActionLabel(project: ProjectActionState): string {
  if (projectHasActiveImport(project)) {
    return "Import in progress";
  }
  if (project.total_images <= 0) {
    return "Import images";
  }
  if (project.processed_images <= 0) {
    return "Process photos";
  }
  if (project.processed_images < project.total_images) {
    return "Continue culling";
  }
  return "Review culling";
}

export function projectProgressSummary(project: ProjectProgressState): string {
  if (projectHasActiveImport(project)) {
    return `${project.total_images} ${project.total_images === 1 ? "photo" : "photos"} registered; import still running`;
  }

  if (project.total_images <= 0) {
    return "No photos imported yet";
  }

  if (project.processed_images <= 0) {
    return `${project.total_images} ${project.total_images === 1 ? "photo" : "photos"} imported; processing not started`;
  }

  return `${project.processed_images} of ${project.total_images} photos processed`;
}

export function projectWorkflowStepHref(project: ProjectRouteState, step: ProjectWorkflowStep): string {
  if (step === "import") {
    return `/projects/${project.id}/import`;
  }

  if (projectHasActiveImport(project) && (step === "process" || step === "cull")) {
    return `/projects/${project.id}/import`;
  }

  if (project.total_images <= 0) {
    return `/projects/${project.id}/import`;
  }

  if (step === "cull" && project.processed_images <= 0) {
    return `/projects/${project.id}/process`;
  }

  return `/projects/${project.id}/${step}`;
}

export function projectWorkflowStepHint(project: ProjectActionState, step: ProjectWorkflowStep): string {
  if (step === "import") {
    return project.total_images > 0 ? "Add more local images" : "Start with local images";
  }

  if (projectHasActiveImport(project) && (step === "process" || step === "cull")) {
    return "Finish import first";
  }

  if (project.total_images <= 0) {
    return "Import photos first";
  }

  if (step === "process") {
    return project.processed_images > 0 ? "Refresh grouping and ranking" : "Run grouping and ranking";
  }

  if (step === "cull") {
    return project.processed_images > 0 ? "Review recommendations" : "Process photos first";
  }

  return "Export selected statuses";
}
