import type { ProcessingJob, Project } from "./api.ts";

type ProcessingProgressJob = Pick<
  ProcessingJob,
  "failed_items" | "job_type" | "processed_items" | "progress_percent" | "status" | "total_items"
>;

type ProcessingFailureJob = Pick<ProcessingJob, "error_message" | "failed_items" | "job_type">;

type ProcessingProgressProject = Pick<Project, "processed_images" | "total_images">;

type ProcessingJobCandidate = Pick<ProcessingJob, "job_type" | "status">;

type ProcessingActionBlockReason = {
  hasImportedPhotos: boolean;
  isImportRunning: boolean;
  isProcessing: boolean;
};

export function processingStatusLabel(status: ProcessingJob["status"] | null | undefined): string {
  if (!status) {
    return "Ready";
  }
  if (status === "complete_with_errors") {
    return "Complete with errors";
  }
  return status[0].toUpperCase() + status.slice(1);
}

export function processingJobTypeLabel(jobType: string): string {
  if (jobType === "import") {
    return "Import";
  }

  if (jobType === "processing") {
    return "Grouping and ranking";
  }

  if (jobType === "export") {
    return "Export";
  }

  return jobType ? jobType[0].toUpperCase() + jobType.slice(1) : "Job";
}

export function hasActiveProcessingJob(jobs: readonly ProcessingJobCandidate[] | null | undefined): boolean {
  return Boolean(jobs?.some((job) => job.status === "queued" || job.status === "running"));
}

export function activeJobOfType<T extends ProcessingJobCandidate>(
  jobs: readonly T[] | null | undefined,
  jobType: string,
): T | undefined {
  return jobs?.find((job) => job.job_type === jobType && (job.status === "queued" || job.status === "running"));
}

export function activeProcessingJob<T extends ProcessingJobCandidate>(jobs: readonly T[] | null | undefined): T | undefined {
  return activeJobOfType(jobs, "processing");
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
    const noun = job.job_type === "import" ? "files" : "photos";
    return `${job.processed_items} of ${job.total_items} ${noun} · ${job.failed_items} failed · ${processingProgressPercent(job)}%`;
  }
  return `${project?.processed_images ?? 0} of ${project?.total_images ?? 0} processed`;
}

export function processingFailureNotice(job: ProcessingFailureJob | null | undefined): string | null {
  if (!job || job.failed_items <= 0) {
    return null;
  }
  if (job.error_message) {
    return job.error_message;
  }
  const noun = job.job_type === "import" ? (job.failed_items === 1 ? "file" : "files") : job.failed_items === 1 ? "photo" : "photos";
  const verb = job.job_type === "import" ? "imported" : "processed";
  return `${job.failed_items} ${noun} could not be ${verb}.`;
}

export function processingActionBlockMessage({
  hasImportedPhotos,
  isImportRunning,
  isProcessing,
}: ProcessingActionBlockReason): string {
  if (isProcessing) {
    return "Grouping and ranking is already running.";
  }

  if (isImportRunning) {
    return "Wait for import previews and analysis to finish before processing.";
  }

  if (!hasImportedPhotos) {
    return "Import JPEG, PNG, or WebP images before running grouping and ranking.";
  }

  return "";
}
