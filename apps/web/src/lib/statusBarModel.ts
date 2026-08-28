import type { ProcessingJob } from "./api.ts";
import { firstActiveJob, processingJobForDisplay, processingJobTypeLabel, processingProgressPercent, processingStatusLabel } from "./processingProgress.ts";
import { projectIdFromPathname } from "./projectRouting.ts";

type StatusBarJobLabel = Pick<ProcessingJob, "current_step" | "job_type" | "progress_percent" | "status">;
type StatusBarJobCandidate = Pick<ProcessingJob, "id" | "job_type" | "status">;

export function sidecarLabel(connected: boolean | null): string {
  if (connected === true) {
    return "Sidecar connected";
  }
  if (connected === false) {
    return "Sidecar disconnected";
  }
  return "Checking sidecar";
}

export function projectLabel(name: string | null | undefined): string {
  if (typeof name !== "string") {
    return "No project";
  }
  const trimmed = name.trim();
  return trimmed || "No project";
}

export function resolveStatusBarProjectId(
  pathname: string,
  lastOpenedProjectId: string | null | undefined,
): string | null {
  const fromPath = projectIdFromPathname(pathname);
  if (fromPath) {
    return fromPath;
  }
  if (typeof lastOpenedProjectId !== "string") {
    return null;
  }
  const trimmed = lastOpenedProjectId.trim();
  return trimmed || null;
}

export function jobLabel(job: StatusBarJobLabel | null | undefined): string {
  if (!job) {
    return "No active job";
  }
  const step = job.current_step?.trim() || processingStatusLabel(job.status);
  return `${processingJobTypeLabel(job.job_type)} · ${step} · ${processingProgressPercent(job)}%`;
}

export function statusBarJob<T extends StatusBarJobCandidate>(jobs: readonly T[] | null | undefined): T | undefined {
  const active = firstActiveJob(jobs);
  if (active) {
    return active;
  }
  const displayed = processingJobForDisplay(jobs, undefined);
  return displayed ? jobs?.find((job) => job.id === displayed.id) : undefined;
}
