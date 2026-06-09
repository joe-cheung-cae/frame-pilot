"use client";

/* eslint-disable @next/next/no-img-element */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ChangeEvent, useEffect, useState } from "react";
import { FileImage, Loader2, Play, RotateCcw, StopCircle } from "lucide-react";
import { api, assetUrl, Photo } from "@/lib/api";
import {
  type ImportFeedbackTone,
  importLoadRecoveryMessage,
  importPreviewCompletionMessage,
  importProcessBlockMessage,
  importRegistrationMessage,
  importRegistrationTone,
  importSelectionBlockMessage,
  importTerminalStatusMessage,
} from "@/lib/importWorkflow";
import {
  activeJobOfType,
  processingProgressPercent,
  processingProgressSummary,
  processingStatusLabel,
} from "@/lib/processingProgress";
import { invalidateProjectWorkflowQueries } from "@/lib/queryInvalidation";

function pluralize(count: number, singular: string, plural = `${singular}s`) {
  return count === 1 ? singular : plural;
}

const IMPORT_MESSAGE_CLASS: Record<ImportFeedbackTone, string> = {
  neutral: "text-neutral-600",
  success: "text-leaf",
  warning: "text-coral",
};

export function ImportPanel({ projectId }: { projectId: string }) {
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<ImportFeedbackTone>("neutral");
  const [skipped, setSkipped] = useState<{ filename: string; reason: string }[]>([]);
  const [showAllSkipped, setShowAllSkipped] = useState(false);
  const [recentImports, setRecentImports] = useState<Photo[]>([]);
  const [currentImportJobId, setCurrentImportJobId] = useState<string | null>(null);
  const [completedImportJobId, setCompletedImportJobId] = useState<string | null>(null);
  const [lastImportPhotoIds, setLastImportPhotoIds] = useState<string[]>([]);
  const queryClient = useQueryClient();
  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    retry: false,
  });
  const mutation = useMutation({
    mutationFn: (files: readonly File[]) => api.importPhotos(projectId, files),
    onMutate: () => {
      setMessage("");
      setMessageTone("neutral");
      setSkipped([]);
      setShowAllSkipped(false);
      setRecentImports([]);
      setCurrentImportJobId(null);
      setCompletedImportJobId(null);
      setLastImportPhotoIds([]);
    },
    onSuccess: async (result) => {
      setMessage(
        importRegistrationMessage({ importedCount: result.imported.length, skippedCount: result.skipped.length }),
      );
      setMessageTone(
        importRegistrationTone({ importedCount: result.imported.length, skippedCount: result.skipped.length }),
      );
      setSkipped(result.skipped);
      setRecentImports(result.imported);
      setLastImportPhotoIds(result.imported.map((photo) => photo.id));
      setCurrentImportJobId(result.job?.id ?? null);
      await invalidateProjectWorkflowQueries(queryClient, projectId);
    },
  });
  const retryMutation = useMutation({
    mutationFn: (jobId: string) => api.retryJob(projectId, jobId),
    onSuccess: async (job) => {
      setMessage("Retry started. Generating missing previews...");
      setMessageTone("neutral");
      setSkipped([]);
      setShowAllSkipped(false);
      setCurrentImportJobId(job.id);
      setCompletedImportJobId(null);
      await invalidateProjectWorkflowQueries(queryClient, projectId);
    },
  });
  const cancelMutation = useMutation({
    mutationFn: (jobId: string) => api.cancelJob(projectId, jobId),
    onSuccess: async (job) => {
      setMessage("Cancellation requested. Finishing the current safe checkpoint...");
      setMessageTone("neutral");
      setCurrentImportJobId(job.id);
      await invalidateProjectWorkflowQueries(queryClient, projectId);
    },
  });
  const importJobsQuery = useQuery({
    queryKey: ["jobs", projectId, "import-active"],
    queryFn: () => api.listJobs(projectId, { limit: 10, offset: 0 }),
    retry: false,
    refetchInterval: (query) => {
      const jobs = query.state.data;
      return jobs?.some((job) => job.job_type === "import" && (job.status === "queued" || job.status === "running"))
        ? 1000
        : false;
    },
  });
  const currentImportJobQuery = useQuery({
    queryKey: ["job", projectId, currentImportJobId],
    queryFn: () => api.getJob(projectId, currentImportJobId ?? ""),
    enabled: Boolean(currentImportJobId),
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1000 : false;
    },
  });

  useEffect(() => {
    const job = currentImportJobQuery.data;
    if (!job || job.id === completedImportJobId) {
      return;
    }
    if (!["complete", "complete_with_errors", "failed", "cancelled"].includes(job.status)) {
      return;
    }

    setCompletedImportJobId(job.id);
    void (async () => {
      await invalidateProjectWorkflowQueries(queryClient, projectId);
      if (job.status === "failed" || job.status === "cancelled") {
        setMessage("");
        setMessageTone("neutral");
        return;
      }
      const refreshed = await Promise.all(
        lastImportPhotoIds.slice(0, 12).map((photoId) => api.getPhoto(projectId, photoId)),
      );
      setRecentImports(refreshed);
      const completionMessage = importPreviewCompletionMessage(lastImportPhotoIds.length);
      if (completionMessage) {
        setMessage(completionMessage);
        setMessageTone("success");
      }
    })();
  }, [completedImportJobId, currentImportJobQuery.data, lastImportPhotoIds, projectId, queryClient]);

  function onFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length) {
      mutation.mutate(files);
    }
  }

  const visibleSkipped = showAllSkipped ? skipped : skipped.slice(0, 5);
  const activeImportJob = activeJobOfType(importJobsQuery.data, "import");
  const latestImportJob = importJobsQuery.data?.find((job) => job.job_type === "import");
  const importJob = currentImportJobQuery.data ?? activeImportJob ?? mutation.data?.job ?? latestImportJob;
  const isImportRunning = importJob?.status === "queued" || importJob?.status === "running" || mutation.isPending;
  const canProcessProject =
    !isImportRunning &&
    importJob?.status !== "failed" &&
    importJob?.status !== "cancelled" &&
    Boolean(project.data?.total_images || recentImports.length);
  const processBlockMessage = importProcessBlockMessage({
    hasImportedPhotos: Boolean(project.data?.total_images || recentImports.length),
    importStatus: importJob?.status,
    isImportRunning,
  });
  const canRetryImport = Boolean(importJob?.retryable) && !isImportRunning && !retryMutation.isPending;
  const importSelectionBlock = importSelectionBlockMessage({
    isCancelling: cancelMutation.isPending,
    isImportRunning,
    isRetrying: retryMutation.isPending,
  });
  const importSelectionDisabled = Boolean(importSelectionBlock);
  const canCancelImport =
    Boolean(importJob) &&
    importJob?.job_type === "import" &&
    (importJob.status === "queued" || importJob.status === "running") &&
    !importJob.cancellation_requested &&
    !cancelMutation.isPending;
  const importProgress = processingProgressPercent(importJob);
  const importTerminalMessage = importTerminalStatusMessage({
    retryable: Boolean(importJob?.retryable),
    status: importJob?.status,
  });
  const importStatusError = currentImportJobQuery.error ?? importJobsQuery.error;
  const importStatusErrorMessage =
    importStatusError instanceof Error ? importStatusError.message : "Import status is unavailable.";

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">{project.data?.name ?? "Project"}</p>
        <h1 className="mt-1 text-3xl font-semibold">Import Images</h1>
        {project.data?.root_path ? (
          <p className="mt-2 break-all text-sm text-neutral-600">Project data: {project.data.root_path}</p>
        ) : null}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <label
          className={`focus-within:ring-2 focus-within:ring-leaf grid min-h-56 place-items-center rounded border border-dashed border-line bg-white p-8 text-center ${
            importSelectionDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
          }`}
        >
          <input
            className="sr-only"
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            disabled={importSelectionDisabled}
            onChange={onFiles}
          />
          <span className="grid gap-3">
            <FileImage className="mx-auto text-leaf" size={34} />
            <span className="font-medium">Choose image files</span>
            <span className="text-sm text-neutral-600">JPEG, PNG, and WebP are supported.</span>
          </span>
        </label>
        <label
          className={`focus-within:ring-2 focus-within:ring-leaf grid min-h-56 place-items-center rounded border border-dashed border-line bg-white p-8 text-center ${
            importSelectionDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
          }`}
        >
          <input
            className="sr-only"
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            disabled={importSelectionDisabled}
            onChange={onFiles}
            {...{ webkitdirectory: "", directory: "" }}
          />
          <span className="grid gap-3">
            <FileImage className="mx-auto text-leaf" size={34} />
            <span className="font-medium">Choose a folder</span>
            <span className="text-sm text-neutral-600">Original files are copied into the local project folder.</span>
            <span className="text-sm text-neutral-600">Source folders are not tracked for rescan yet.</span>
          </span>
        </label>
      </div>
      {importSelectionBlock ? <p className="text-sm text-neutral-600">{importSelectionBlock}</p> : null}
      {mutation.isPending ? (
        <p className="inline-flex items-center gap-2 text-sm">
          <Loader2 className="animate-spin" size={16} />
          Uploading and registering files...
        </p>
      ) : null}
      {importJob ? (
        <div className="grid gap-2 rounded border border-line bg-white p-4 text-sm">
          <div className="flex items-center justify-between gap-4">
            <span className="font-medium">Import {processingStatusLabel(importJob.status)}</span>
            <span className="text-neutral-600">{processingProgressSummary(importJob, project.data)}</span>
          </div>
          <p className="text-neutral-700">{importJob.current_step}</p>
          <div className="h-2 rounded bg-mist">
            <div
              className={`h-2 rounded ${importJob.status === "failed" || importJob.status === "cancelled" ? "bg-coral" : "bg-leaf"}`}
              style={{ width: `${importProgress}%` }}
            />
          </div>
          {importTerminalMessage ? <p className="text-neutral-700">{importTerminalMessage}</p> : null}
          {importJob.error_message ? <p className="text-coral">{importJob.error_message}</p> : null}
          {importJob.cancellation_requested && importJob.status !== "cancelled" ? (
            <p className="text-neutral-600">Cancellation requested. FramePilot will stop after a safe checkpoint.</p>
          ) : null}
          {canCancelImport ? (
            <button
              className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line bg-white px-3 py-2 font-medium"
              onClick={() => cancelMutation.mutate(importJob.id)}
              type="button"
            >
              <StopCircle size={16} />
              Cancel Import
            </button>
          ) : null}
          {canRetryImport ? (
            <button
              className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line bg-white px-3 py-2 font-medium"
              onClick={() => retryMutation.mutate(importJob.id)}
              type="button"
            >
              <RotateCcw size={16} />
              Retry Import
            </button>
          ) : null}
        </div>
      ) : null}
      {message ? <p className={`text-sm ${IMPORT_MESSAGE_CLASS[messageTone]}`}>{message}</p> : null}
      {skipped.length ? (
        <div className="rounded border border-line bg-white p-3 text-sm text-neutral-700">
          <p className="font-medium text-coral">
            {skipped.length} {pluralize(skipped.length, "file")} skipped.
          </p>
          <ul className="mt-2 grid gap-1">
            {visibleSkipped.map((item) => (
              <li key={`${item.filename}-${item.reason}`}>
                {item.filename}: {item.reason}
              </li>
            ))}
          </ul>
          {skipped.length > 5 ? (
            <button
              className="focus-ring mt-3 rounded border border-line bg-white px-3 py-2 text-xs font-medium"
              onClick={() => setShowAllSkipped((current) => !current)}
              aria-expanded={showAllSkipped}
            >
              {showAllSkipped ? "Show first 5 skipped files" : `Show all ${skipped.length} skipped files`}
            </button>
          ) : null}
        </div>
      ) : null}
      {recentImports.length ? (
        <div className="grid gap-3 rounded border border-line bg-white p-4">
          <h2 className="text-sm font-semibold">Recently Imported</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {recentImports.slice(0, 12).map((photo) => {
              const thumbnail = assetUrl(projectId, photo.thumbnail_path);
              return (
                <div className="overflow-hidden rounded border border-line bg-mist" key={photo.id}>
                  {thumbnail ? (
                    <img
                      className="aspect-[4/3] w-full object-cover"
                      src={thumbnail}
                      alt={`Thumbnail for ${photo.filename}`}
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="grid aspect-[4/3] place-items-center text-xs text-neutral-600">No preview</div>
                  )}
                  <p className="truncate px-2 py-1 text-xs text-neutral-700">{photo.filename}</p>
                </div>
              );
            })}
          </div>
          {recentImports.length > 12 ? (
            <p className="text-sm text-neutral-600">Showing the first 12 imported images.</p>
          ) : null}
        </div>
      ) : null}
      {mutation.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{mutation.error.message}</p>
          <p className="text-neutral-600">{importLoadRecoveryMessage("import")}</p>
        </div>
      ) : null}
      {cancelMutation.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{cancelMutation.error.message}</p>
          <p className="text-neutral-600">{importLoadRecoveryMessage("cancel")}</p>
        </div>
      ) : null}
      {retryMutation.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{retryMutation.error.message}</p>
          <p className="text-neutral-600">{importLoadRecoveryMessage("retry")}</p>
        </div>
      ) : null}
      {currentImportJobQuery.isError || importJobsQuery.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">Could not load import status: {importStatusErrorMessage}</p>
          <p className="text-neutral-600">{importLoadRecoveryMessage("job")}</p>
        </div>
      ) : null}
      {project.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{project.error.message}</p>
          <p className="text-neutral-600">{importLoadRecoveryMessage("project")}</p>
        </div>
      ) : null}
      {canProcessProject ? (
        <Link
          className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-white"
          href={`/projects/${projectId}/process`}
        >
          <Play size={18} />
          Process Project
        </Link>
      ) : (
        <div className="grid gap-2">
          <button
            className="inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-white opacity-50"
            disabled
            type="button"
          >
            <Play size={18} />
            Process Project
          </button>
          {processBlockMessage ? <p className="text-sm text-neutral-600">{processBlockMessage}</p> : null}
        </div>
      )}
    </section>
  );
}
