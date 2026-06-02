import type { Project } from "@/lib/api";

export function projectNextHref(project: Pick<Project, "id" | "total_images" | "processed_images">): string {
  if (project.total_images <= 0) {
    return `/projects/${project.id}/import`;
  }
  if (project.processed_images > 0) {
    return `/projects/${project.id}/cull`;
  }
  return `/projects/${project.id}/process`;
}
