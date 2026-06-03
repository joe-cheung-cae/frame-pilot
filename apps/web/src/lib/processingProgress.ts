import type { ProcessingJob, Project } from "./api.ts";

type ProcessingProgressJob = Pick<
  ProcessingJob,
  "failed_items" | "processed_items" | "progress_percent" | "status" | "total_items"
>;

type ProcessingProgressProject = Pick<Project, "processed_images" | "total_images">;

type ProcessingJobCandidate = Pick<ProcessingJob, "job_type" | "status">;

export function processingStatusLabel(status: ProcessingJob["status"] | null | undefined): string {
  return status ? status[0].toUpperCase() + status.slice(1) : "Ready";
}

export function activeProcessingJob<T extends ProcessingJobCandidate>(jobs: readonly T[] | null | undefined): T | undefined {
  return jobs?.find((job) => job.job_type === "processing" && (job.status === "queued" || job.status === "running"));
}

export function processingProgressPercent(job: Pick<ProcessingJob, "progress_percent"> | null | undefined): number {
  if (!job) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round(job.progress_percent)));
}

export function processingProgressSummary(
  job: ProcessingProgressJob | null | undefined,
  project: ProcessingProgressProject | null | undefined,
): string {
  if (job) {
    return `${job.processed_items} of ${job.total_items} photos · ${job.failed_items} failed · ${processingProgressPercent(job)}%`;
  }
  return `${project?.processed_images ?? 0} of ${project?.total_images ?? 0} processed`;
}
