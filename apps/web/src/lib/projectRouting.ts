import type { Project } from "@/lib/api";

type ActiveImportState = { status?: string } | null | undefined;
type ProjectRouteState = Pick<Project, "id" | "total_images" | "processed_images"> & {
  active_import_job?: ActiveImportState;
};
type ProjectActionState = Pick<Project, "total_images" | "processed_images"> & {
  active_import_job?: ActiveImportState;
};

export function projectHasActiveImport(project: { active_import_job?: ActiveImportState }): boolean {
  const status = project.active_import_job?.status;
  return status === "queued" || status === "running";
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
