"use client";

/* eslint-disable @next/next/no-img-element */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChangeEvent, useEffect, useRef, useState } from "react";
import { FileImage, Loader2, Play, RotateCcw, StopCircle } from "lucide-react";
import { api, assetUrl, Photo } from "@/lib/api";
import {
  type ImportFeedbackTone,
  importLoadRecoveryMessage,
  importPathProgressMessage,
  importPreviewCompletionMessage,
  importProcessBlockMessage,
  importRegistrationMessage,
  importRegistrationTone,
  importSelectionBlockMessage,
  importTerminalStatusMessage,
  loadAvailableImportedPhotosForJob,
} from "@/lib/importWorkflow";
import {
  collectDroppedPaths,
  importDropOverlayPointerEvents,
  type NativeDragDropEvent,
} from "@/lib/droppedPaths";
import { getNativeFs } from "@/lib/nativeFs";
import { Link } from "@/lib/navigation";
import { isDesktopShell } from "@/lib/shell";
import { copyForShell } from "@/lib/shellCopy";
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

export const IMPORT_IMAGE_ACCEPT =
  "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif,image/avif,.avif,image/x-adobe-dng,.dng,image/x-sony-arw,.arw,image/x-canon-cr3,.cr3,image/x-nikon-nef,.nef";
const IMPORT_FORMAT_COPY =
  "JPEG, PNG, WebP, HEIC/HEIF, AVIF, and RAW with an embedded preview are supported. RAW without a preview is skipped.";

const IMPORT_MESSAGE_CLASS: Record<ImportFeedbackTone, string> = {
  neutral: "text-muted",
  success: "text-leaf",
  warning: "text-coral",
};

type ImportRequest = { files: readonly File[] } | { paths: readonly string[] };

export function ImportPanel({ projectId }: { projectId: string }) {
  const desktopShell = isDesktopShell();
  const copy = copyForShell(desktopShell);
  const nativeFs = getNativeFs();
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<ImportFeedbackTone>("neutral");
  const [skipped, setSkipped] = useState<{ filename: string; reason: string }[]>([]);
  const [showAllSkipped, setShowAllSkipped] = useState(false);
  const [recentImports, setRecentImports] = useState<Photo[]>([]);
  const [currentImportJobId, setCurrentImportJobId] = useState<string | null>(null);
  const currentImportJobIdRef = useRef<string | null>(null);
  const [completedImportJobId, setCompletedImportJobId] = useState<string | null>(null);
  const [lastImportPhotoIds, setLastImportPhotoIds] = useState<string[]>([]);
  const [importMode, setImportMode] = useState<"upload" | "paths">("upload");
  const [dragActive, setDragActive] = useState(false);
  const dragDepthRef = useRef(0);
  const dropHandledRef = useRef(false);
  const importDroppedPathsRef = useRef<(paths: readonly string[]) => void>(() => {});
  const queryClient = useQueryClient();

  function selectCurrentImportJob(jobId: string | null) {
    currentImportJobIdRef.current = jobId;
    setCurrentImportJobId(jobId);
  }

  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    retry: false,
  });
  const mutation = useMutation({
    mutationFn: (request: ImportRequest) => {
      if ("paths" in request) {
        return api.importPhotosFromPaths(projectId, request.paths, {
          onSliceComplete: (result) => {
            if (result.job?.id) {
              selectCurrentImportJob(result.job.id);
            }
            setMessage(importPathProgressMessage(result));
            setMessageTone("neutral");
          },
        });
      }
      return api.importPhotos(projectId, request.files, {
        onBatchComplete: (result, batchIndex, batchCount) => {
          if (result.job?.id) {
            selectCurrentImportJob(result.job.id);
          }
          setMessage(
            `Uploading batch ${batchIndex + 1} of ${batchCount}. ${result.imported.length} files accepted in this batch.`,
          );
          setMessageTone("neutral");
        },
      });
    },
    onMutate: (request) => {
      setImportMode("paths" in request ? "paths" : "upload");
      setMessage("");
      setMessageTone("neutral");
      setSkipped([]);
      setShowAllSkipped(false);
      setRecentImports([]);
      selectCurrentImportJob(null);
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
      selectCurrentImportJob(result.job?.id ?? null);
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
      selectCurrentImportJob(job.id);
      setCompletedImportJobId(null);
      await invalidateProjectWorkflowQueries(queryClient, projectId);
    },
  });
  const cancelMutation = useMutation({
    mutationFn: (jobId: string) => api.cancelJob(projectId, jobId),
    onSuccess: async (job) => {
      setMessage("Cancellation requested. Finishing the current safe checkpoint...");
      setMessageTone("neutral");
      selectCurrentImportJob(job.id);
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
      if (currentImportJobIdRef.current !== job.id) {
        return;
      }
      if (job.status === "failed" || job.status === "cancelled") {
        setMessage("");
        setMessageTone("neutral");
        return;
      }
      const refreshed = await loadAvailableImportedPhotosForJob(
        job.id,
        lastImportPhotoIds,
        (photoId) => api.getPhoto(projectId, photoId),
        () => currentImportJobIdRef.current,
      );
      if (!refreshed) return;
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
      mutation.mutate({ files });
    }
  }

  async function onPickImageFiles() {
    if (!nativeFs) {
      return;
    }
    try {
      const picked = await nativeFs.pickImageFiles();
      if (picked?.length) {
        mutation.mutate({ paths: picked });
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
      setMessageTone("warning");
    }
  }

  async function onPickFolder() {
    if (!nativeFs) {
      return;
    }
    try {
      const picked = await nativeFs.pickDirectory();
      if (picked) {
        mutation.mutate({ paths: [picked] });
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
      setMessageTone("warning");
    }
  }

  const visibleSkipped = showAllSkipped ? skipped : skipped.slice(0, 5);
  const activeImportJob = activeJobOfType(importJobsQuery.data, "import");
  const latestImportJob = importJobsQuery.data?.find((job) => job.job_type === "import");
  const importJob = currentImportJobQuery.data ?? activeImportJob ?? mutation.data?.job ?? latestImportJob;
  const isImportRunning = importJob?.status === "queued" || importJob?.status === "running" || mutation.isPending;
  const hasImportedPhotos = Boolean(project.data?.total_images || recentImports.length);
  const processBlockMessage = importProcessBlockMessage({
    hasImportedPhotos,
    importStatus: importJob?.status,
    isImportRunning,
  });
  const canProcessProject = !processBlockMessage;
  const canRetryImport = Boolean(importJob?.retryable) && !isImportRunning && !retryMutation.isPending;
  const importSelectionBlock = importSelectionBlockMessage({
    isCancelling: cancelMutation.isPending,
    isImportRunning,
    isRetrying: retryMutation.isPending,
  });
  const importSelectionDisabled = Boolean(importSelectionBlock);
  importDroppedPathsRef.current = (paths) => {
    if (!paths.length || importSelectionDisabled || dropHandledRef.current) {
      return;
    }
    // HTML5 and Tauri can fire for the same drop; keep the first path list.
    dropHandledRef.current = true;
    window.setTimeout(() => {
      dropHandledRef.current = false;
    }, 400);
    mutation.mutate({ paths: [...paths] });
  };

  useEffect(() => {
    function isFileDrag(event: DragEvent): boolean {
      const transfer = event.dataTransfer;
      if (!transfer) {
        return false;
      }
      const types = transfer.types ? Array.from(transfer.types as ArrayLike<string>) : [];
      if (types.includes("Files") || types.includes("text/uri-list") || types.includes("application/x-moz-file")) {
        return true;
      }
      return (transfer.files?.length ?? 0) > 0;
    }

    function clearDrag() {
      dragDepthRef.current = 0;
      setDragActive(false);
    }

    function onDragEnter(event: DragEvent) {
      if (!isFileDrag(event)) {
        return;
      }
      event.preventDefault();
      dragDepthRef.current += 1;
      setDragActive(true);
    }

    function onDragOver(event: DragEvent) {
      if (!isFileDrag(event)) {
        return;
      }
      event.preventDefault();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = "copy";
      }
      setDragActive(true);
    }

    function onDragLeave(event: DragEvent) {
      if (!isFileDrag(event)) {
        return;
      }
      if (event.relatedTarget == null) {
        clearDrag();
        return;
      }
      dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
      if (dragDepthRef.current === 0) {
        setDragActive(false);
      }
    }

    function onDrop(event: DragEvent) {
      const paths = collectDroppedPaths(event);
      if (!isFileDrag(event) && paths.length === 0) {
        clearDrag();
        return;
      }
      event.preventDefault();
      clearDrag();
      importDroppedPathsRef.current(paths);
    }

    window.addEventListener("dragenter", onDragEnter);
    window.addEventListener("dragover", onDragOver);
    window.addEventListener("dragleave", onDragLeave);
    window.addEventListener("drop", onDrop);
    return () => {
      window.removeEventListener("dragenter", onDragEnter);
      window.removeEventListener("dragover", onDragOver);
      window.removeEventListener("dragleave", onDragLeave);
      window.removeEventListener("drop", onDrop);
    };
  }, []);

  useEffect(() => {
    if (!nativeFs?.subscribeDragDrop) {
      return;
    }
    let cancelled = false;
    let unlisten: (() => void) | undefined;
    void nativeFs
      .subscribeDragDrop((event: NativeDragDropEvent) => {
        if (cancelled) {
          return;
        }
        if (event.type === "enter" || event.type === "over") {
          setDragActive(true);
          return;
        }
        dragDepthRef.current = 0;
        setDragActive(false);
        if (event.type === "drop") {
          importDroppedPathsRef.current(event.paths);
        }
      })
      .then((stop) => {
        if (cancelled) {
          stop();
          return;
        }
        unlisten = stop;
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      unlisten?.();
    };
  }, [nativeFs]);

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
    <section className="relative mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div
        aria-hidden={!dragActive}
        className={`absolute inset-0 z-10 grid place-items-center rounded text-center ${
          dragActive ? "border-2 border-dashed border-leaf bg-surface/80" : ""
        }`}
        data-testid="import-drop-overlay"
        style={{ pointerEvents: importDropOverlayPointerEvents(dragActive) }}
      >
        {dragActive ? <p className="font-medium">Drop files or folders to import</p> : null}
      </div>
      <div>
        <p className="text-sm text-muted">{project.data?.name ?? "Project"}</p>
        <h1 className="mt-1 text-3xl font-semibold">Import Images</h1>
        {project.data?.root_path ? (
          <p className="mt-2 break-all text-sm text-muted">Project data: {project.data.root_path}</p>
        ) : null}
      </div>
      {desktopShell ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <button
            className={`focus-within:ring-2 focus-within:ring-leaf grid min-h-56 place-items-center rounded border border-dashed border-line bg-surface p-8 text-center ${
              importSelectionDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
            }`}
            disabled={importSelectionDisabled}
            onClick={() => {
              void onPickImageFiles();
            }}
            type="button"
          >
            <span className="grid gap-3">
              <FileImage className="mx-auto text-leaf" size={34} />
              <span className="font-medium">Choose image files</span>
              <span className="text-sm text-muted">{IMPORT_FORMAT_COPY}</span>
            </span>
          </button>
          <button
            className={`focus-within:ring-2 focus-within:ring-leaf grid min-h-56 place-items-center rounded border border-dashed border-line bg-surface p-8 text-center ${
              importSelectionDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
            }`}
            disabled={importSelectionDisabled}
            onClick={() => {
              void onPickFolder();
            }}
            type="button"
          >
            <span className="grid gap-3">
              <FileImage className="mx-auto text-leaf" size={34} />
              <span className="font-medium">{copy.chooseFolder}</span>
              <span className="text-sm text-muted">Original files are copied into the local project folder.</span>
              <span className="text-sm text-muted">Source folders are not tracked for rescan yet.</span>
            </span>
          </button>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          <label
            className={`focus-within:ring-2 focus-within:ring-leaf grid min-h-56 place-items-center rounded border border-dashed border-line bg-surface p-8 text-center ${
              importSelectionDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
            }`}
          >
            <input
              className="sr-only"
              type="file"
              multiple
              accept={IMPORT_IMAGE_ACCEPT}
              disabled={importSelectionDisabled}
              onChange={onFiles}
            />
            <span className="grid gap-3">
              <FileImage className="mx-auto text-leaf" size={34} />
              <span className="font-medium">Choose image files</span>
              <span className="text-sm text-muted">{IMPORT_FORMAT_COPY}</span>
            </span>
          </label>
          <label
            className={`focus-within:ring-2 focus-within:ring-leaf grid min-h-56 place-items-center rounded border border-dashed border-line bg-surface p-8 text-center ${
              importSelectionDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
            }`}
          >
            <input
              className="sr-only"
              type="file"
              multiple
              accept={IMPORT_IMAGE_ACCEPT}
              disabled={importSelectionDisabled}
              onChange={onFiles}
              {...{ webkitdirectory: "", directory: "" }}
            />
            <span className="grid gap-3">
              <FileImage className="mx-auto text-leaf" size={34} />
              <span className="font-medium">{copy.chooseFolder}</span>
              <span className="text-sm text-muted">Original files are copied into the local project folder.</span>
              <span className="text-sm text-muted">Source folders are not tracked for rescan yet.</span>
            </span>
          </label>
        </div>
      )}
      {importSelectionBlock ? <p className="text-sm text-muted">{importSelectionBlock}</p> : null}
      {mutation.isPending ? (
        <p className="inline-flex items-center gap-2 text-sm">
          <Loader2 className="animate-spin" size={16} />
          {importMode === "paths" ? "Registering local files..." : "Uploading and registering files..."}
        </p>
      ) : null}
      {importJob ? (
        <div className="grid gap-2 rounded border border-line bg-surface p-4 text-sm">
          <div className="flex items-center justify-between gap-4">
            <span className="font-medium">Import {processingStatusLabel(importJob.status)}</span>
            <span className="text-muted">{processingProgressSummary(importJob, project.data)}</span>
          </div>
          <p className="text-muted">{importJob.current_step}</p>
          <div className="h-2 rounded bg-mist">
            <div
              className={`h-2 rounded ${importJob.status === "failed" || importJob.status === "cancelled" ? "bg-coral" : "bg-leaf"}`}
              style={{ width: `${importProgress}%` }}
            />
          </div>
          {importTerminalMessage ? <p className="text-muted">{importTerminalMessage}</p> : null}
          {importJob.error_message ? <p className="text-coral">{importJob.error_message}</p> : null}
          {importJob.cancellation_requested && importJob.status !== "cancelled" ? (
            <p className="text-muted">Cancellation requested. FramePilot will stop after a safe checkpoint.</p>
          ) : null}
          {canCancelImport ? (
            <button
              className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line bg-surface px-3 py-2 font-medium"
              onClick={() => cancelMutation.mutate(importJob.id)}
              type="button"
            >
              <StopCircle size={16} />
              Cancel Import
            </button>
          ) : null}
          {canRetryImport ? (
            <button
              className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line bg-surface px-3 py-2 font-medium"
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
        <div className="rounded border border-line bg-surface p-3 text-sm text-muted">
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
              className="focus-ring mt-3 rounded border border-line bg-surface px-3 py-2 text-xs font-medium"
              onClick={() => setShowAllSkipped((current) => !current)}
              aria-expanded={showAllSkipped}
            >
              {showAllSkipped ? "Show first 5 skipped files" : `Show all ${skipped.length} skipped files`}
            </button>
          ) : null}
        </div>
      ) : null}
      {recentImports.length ? (
        <div className="grid gap-3 rounded border border-line bg-surface p-4">
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
                    <div className="grid aspect-[4/3] place-items-center text-xs text-muted">No preview</div>
                  )}
                  <p className="truncate px-2 py-1 text-xs text-muted">{photo.filename}</p>
                </div>
              );
            })}
          </div>
          {recentImports.length > 12 ? (
            <p className="text-sm text-muted">Showing the first 12 imported images.</p>
          ) : null}
        </div>
      ) : null}
      {mutation.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{mutation.error.message}</p>
          <p className="text-muted">{copy.importLoadRetryHint}</p>
        </div>
      ) : null}
      {cancelMutation.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{cancelMutation.error.message}</p>
          <p className="text-muted">{importLoadRecoveryMessage("cancel")}</p>
        </div>
      ) : null}
      {retryMutation.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{retryMutation.error.message}</p>
          <p className="text-muted">{importLoadRecoveryMessage("retry")}</p>
        </div>
      ) : null}
      {currentImportJobQuery.isError || importJobsQuery.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">Could not load import status: {importStatusErrorMessage}</p>
          <p className="text-muted">{importLoadRecoveryMessage("job")}</p>
        </div>
      ) : null}
      {project.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{project.error.message}</p>
          <p className="text-muted">{importLoadRecoveryMessage("project")}</p>
        </div>
      ) : null}
      {canProcessProject ? (
        <Link
          className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-mist"
          href={`/projects/${projectId}/process`}
        >
          <Play size={18} />
          Process Project
        </Link>
      ) : (
        <div className="grid gap-2">
          <button
            className="inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-mist opacity-50"
            disabled
            type="button"
          >
            <Play size={18} />
            Process Project
          </button>
          {processBlockMessage ? <p className="text-sm text-muted">{processBlockMessage}</p> : null}
        </div>
      )}
    </section>
  );
}
