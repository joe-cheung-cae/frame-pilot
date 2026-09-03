import type { ProcessingJob, Project } from "./api.ts";

type ProcessingProgressJob = Pick<
  ProcessingJob,
  "failed_items" | "job_type" | "processed_items" | "progress_percent" | "status" | "total_items"
>;

type ProcessingFailureJob = Pick<ProcessingJob, "error_message" | "failed_items" | "job_type">;

type ProcessingRecoveryReason = {
  failedItems: number;
  retryable: boolean;
  status: ProcessingJob["status"] | null | undefined;
};

type ProcessingLoadScope = "cancel" | "history" | "job" | "project";

type ProcessingProgressProject = Pick<Project, "processed_images" | "total_images">;

type ProcessingJobCandidate = Pick<ProcessingJob, "job_type" | "status">;
type ProcessingDisplayJobCandidate = ProcessingJobCandidate & Pick<ProcessingJob, "id">;

type ProcessingCancelJobCandidate = Pick<ProcessingJob, "cancellation_requested" | "job_type" | "status">;

type ProcessingActionBlockReason = {
  hasImportedPhotos: boolean;
  isCancelling?: boolean;
  isImportRunning: boolean;
  isProcessing: boolean;
};

type ProcessingCancelPendingReason = {
  cancellationRequested?: boolean;
  isCancelPending?: boolean;
  status?: ProcessingJob["status"] | null;
};

function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return count === 1 ? singular : plural;
}

export function processingStatusLabel(status: ProcessingJob["status"] | null | undefined): string {
  if (!status) {
    return "Ready";
  }
  if (status === "complete_with_errors") {
    return "Complete with errors";
  }
  return status[0].toUpperCase() + status.slice(1);
}

export function processingJobHasReviewableResults(status: ProcessingJob["status"] | null | undefined): boolean {
  return status === "complete" || status === "complete_with_errors";
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

export function firstActiveJob<T extends ProcessingJobCandidate>(jobs: readonly T[] | null | undefined): T | undefined {
  return jobs?.find((job) => job.status === "queued" || job.status === "running");
}

export function hasActiveProcessingJob(jobs: readonly ProcessingJobCandidate[] | null | undefined): boolean {
  return Boolean(firstActiveJob(jobs));
}

export function activeJobOfType<T extends ProcessingJobCandidate>(
  jobs: readonly T[] | null | undefined,
  jobType: string,
): T | undefined {
  return firstActiveJob(jobs?.filter((job) => job.job_type === jobType));
}

export function jobsRefetchIntervalMs(jobs: readonly ProcessingJobCandidate[] | null | undefined): number {
  return hasActiveProcessingJob(jobs) ? 1000 : 5000;
}

export function activeProcessingJob<T extends ProcessingJobCandidate>(
  jobs: readonly T[] | null | undefined,
): T | undefined {
  return activeJobOfType(jobs, "processing");
}

export function processingJobForDisplay<
  THistoryJob extends ProcessingDisplayJobCandidate,
  TStartedJob extends ProcessingDisplayJobCandidate,
>(
  jobs: readonly THistoryJob[] | null | undefined,
  startedJob: TStartedJob | null | undefined,
): THistoryJob | TStartedJob | undefined {
  const activeJob = activeProcessingJob(jobs);
  if (activeJob) return activeJob;

  const startedJobInHistory = startedJob && jobs?.some((job) => job.id === startedJob.id);
  if (startedJob && !startedJobInHistory) return startedJob;

  return jobs?.find((job) => job.job_type === "processing") ?? startedJob ?? undefined;
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
    const noun = job.job_type === "import" ? pluralize(job.total_items, "file") : pluralize(job.total_items, "photo");
    const parts = [`${job.processed_items} of ${job.total_items} ${noun}`];
    if (job.failed_items > 0) {
      parts.push(`${job.failed_items} failed`);
    }
    parts.push(`${processingProgressPercent(job)}%`);
    return parts.join(" · ");
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
  const noun =
    job.job_type === "import"
      ? job.failed_items === 1
        ? "file"
        : "files"
      : job.failed_items === 1
        ? "photo"
        : "photos";
  const verb = job.job_type === "import" ? "imported" : "processed";
  return `${job.failed_items} ${noun} could not be ${verb}.`;
}

export function processingRecoveryMessage({ failedItems, retryable, status }: ProcessingRecoveryReason): string {
  if (status === "failed") {
    return retryable
      ? "Retry will rebuild local grouping and ranking metadata without modifying original files."
      : "Imported files remain safe. Reimport affected images or resolve failed local files before running again.";
  }

  if (status === "cancelled") {
    return "Processing stopped at a safe checkpoint. Run grouping and ranking again when you are ready.";
  }

  if (status === "complete_with_errors" && failedItems > 0) {
    return `Successfully processed photos are ready for culling. Review ${failedItems} failed ${pluralize(
      failedItems,
      "photo",
    )} before exporting a final set.`;
  }

  return "";
}

export function processingLoadRecoveryMessage(scope: ProcessingLoadScope): string {
  if (scope === "job") {
    return "Confirm the local FramePilot API is running, then reload processing status. Existing local job records remain in the project database.";
  }

  if (scope === "history") {
    return "Confirm the local FramePilot API is running, then reload job history. Project data stays on this computer.";
  }

  if (scope === "cancel") {
    return "Confirm the local FramePilot API is running. If cancellation did not reach the job, FramePilot will keep the original files unchanged.";
  }

  return "Confirm the local FramePilot API is running, then reload this processing page. Imported originals remain unchanged.";
}

export function canCancelProcessing(
  job: ProcessingCancelJobCandidate | null | undefined,
  isCancelPending: boolean,
): boolean {
  return Boolean(
    job &&
    job.job_type === "processing" &&
    (job.status === "queued" || job.status === "running") &&
    !job.cancellation_requested &&
    !isCancelPending,
  );
}

export function processingCancelPendingMessage({
  cancellationRequested = false,
  isCancelPending = false,
  status,
}: ProcessingCancelPendingReason): string {
  if (status !== "queued" && status !== "running") {
    return "";
  }
  if (!isCancelPending && !cancellationRequested) {
    return "";
  }
  return "Cancellation requested. FramePilot will stop after a safe checkpoint.";
}

export function processingActionBlockMessage({
  hasImportedPhotos,
  isCancelling = false,
  isImportRunning,
  isProcessing,
}: ProcessingActionBlockReason): string {
  if (isCancelling) {
    return "Cancellation is being requested. Wait for FramePilot to reach a safe checkpoint.";
  }

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
