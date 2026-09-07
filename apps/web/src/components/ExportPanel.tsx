"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  ClipboardCopy,
  Download,
  FileArchive,
  FileSpreadsheet,
  FolderOpen,
  FolderOutput,
  Loader2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, exportDownloadUrl, type ExportRecord } from "@/lib/api";
import {
  EXPORT_STATUSES,
  exportActionBlockMessage,
  exportActionRecoveryMessage,
  exportLoadRecoveryMessage,
  exportRecoveryMessage,
  exportSelectedCountLabel,
  exportStatusCountLabel,
  formatExportRecordStatus,
  formatExportStatusSummary,
  hasRunningExport,
  isExportDownloadable,
  selectedPhotoCount,
  type ExportStatus,
} from "@/lib/exportSelection";
import { getNativeFs } from "@/lib/nativeFs";
import { invalidateProjectExportQueries } from "@/lib/queryInvalidation";
import { projectExportRoot, revealFolder } from "@/lib/revealFolder";
import { isDesktopShell } from "@/lib/shell";
import { copyForShell } from "@/lib/shellCopy";
import {
  DEFAULT_EXPORT_STATUS_PREFERENCE,
  exportPreferenceMessageTone,
  loadExportStatusPreference,
  toggleExportStatusPreferenceWithMessage,
} from "@/lib/settings";

type Mode = "csv" | "folder" | "zip";

const RECENT_EXPORT_LIMIT = 50;
const PREFERENCE_MESSAGE_CLASS = {
  neutral: "text-muted",
  success: "text-leaf",
  warning: "text-coral",
} as const;

function photoCountLabel(count: number) {
  return `${count} ${count === 1 ? "photo" : "photos"}`;
}

export function ExportPanel({ projectId }: { projectId: string }) {
  const nativeFs = getNativeFs();
  const desktopShell = isDesktopShell();
  const copy = copyForShell(desktopShell);
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<Mode>("csv");
  const [includeXmp, setIncludeXmp] = useState(false);
  const [statuses, setStatuses] = useState<ExportStatus[]>(DEFAULT_EXPORT_STATUS_PREFERENCE);
  const [exportLimit, setExportLimit] = useState(RECENT_EXPORT_LIMIT);
  const [copiedPath, setCopiedPath] = useState("");
  const [copyError, setCopyError] = useState("");
  const [preferenceMessage, setPreferenceMessage] = useState("");
  const exportHistoryQueryKey = ["exports", projectId, exportLimit];
  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    retry: false,
  });
  const statusCountsQuery = useQuery({
    queryKey: ["photo-status-counts", projectId],
    queryFn: () => api.getPhotoStatusCounts(projectId),
    retry: false,
  });
  const exportsQuery = useQuery({
    queryKey: exportHistoryQueryKey,
    queryFn: () => api.listExports(projectId, { limit: exportLimit, offset: 0 }),
    retry: false,
    refetchInterval: (query) => (hasRunningExport(query.state.data ?? []) ? 1000 : false),
  });
  const statusCounts = statusCountsQuery.data ?? { Pick: 0, Maybe: 0, Reject: 0, Unreviewed: 0 };
  const selectedCount = selectedPhotoCount(statusCounts, statuses);
  const statusCountsLoading = statusCountsQuery.isLoading;
  const canLoadMoreExports = (exportsQuery.data?.length ?? 0) >= exportLimit;

  useEffect(() => {
    setStatuses(loadExportStatusPreference());
  }, []);

  const mutation = useMutation({
    mutationFn: () => {
      if (!statuses.length || selectedCount === 0) {
        throw new Error("Choose at least one non-empty status before exporting.");
      }
      return api.exportSelection(projectId, mode, statuses, includeXmp);
    },
    onError: () => {
      void invalidateProjectExportQueries(queryClient, projectId);
    },
    onSuccess: (record) => {
      queryClient.setQueryData(exportHistoryQueryKey, (current: unknown) =>
        Array.isArray(current) ? [record, ...current] : [record],
      );
      void invalidateProjectExportQueries(queryClient, projectId);
    },
  });
  const exportBlockMessage = exportActionBlockMessage({
    isExporting: mutation.isPending,
    isStatusCountsLoading: statusCountsLoading,
    selectedCount,
    selectedStatuses: statuses,
  });
  const exportControlsDisabled = mutation.isPending;

  function toggleStatus(status: ExportStatus) {
    setStatuses((current) => {
      const result = toggleExportStatusPreferenceWithMessage(current, status);
      setPreferenceMessage(result.message);
      return result.statuses;
    });
  }

  async function copyPath(path: string) {
    try {
      await navigator.clipboard.writeText(path);
      setCopiedPath(path);
      setCopyError("");
    } catch {
      setCopyError("Could not copy export path.");
    }
  }

  function copyPathButton(path: string) {
    const isCopied = copiedPath === path;
    return (
      <button
        className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line px-3 py-2 font-medium"
        onClick={() => void copyPath(path)}
        type="button"
      >
        {isCopied ? <Check size={16} /> : <ClipboardCopy size={16} />}
        {isCopied ? "Path Copied" : "Copy Path"}
      </button>
    );
  }

  const exportOutputPath =
    mutation.data?.output_path ?? exportsQuery.data?.find((record) => record.output_path)?.output_path;

  function openExportFolder(outputPath?: string) {
    if (!nativeFs) {
      return;
    }
    void revealFolder(
      "export",
      { outputPath: outputPath ?? exportOutputPath, rootPath: projectQuery.data?.root_path },
      nativeFs.revealInFileManager,
    );
  }

  function openExportFolderButton(outputPath?: string) {
    if (!nativeFs) {
      return null;
    }
    return (
      <button
        className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line px-3 py-2 font-medium"
        onClick={() => openExportFolder(outputPath)}
        type="button"
      >
        <FolderOpen size={16} />
        Open export folder
      </button>
    );
  }

  function showInFolderButton(outputPath: string) {
    if (!nativeFs) {
      return null;
    }
    return (
      <button
        className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line px-3 py-2 font-medium"
        onClick={() => {
          void revealFolder(
            "export",
            { outputPath, rootPath: projectQuery.data?.root_path },
            nativeFs.revealInFileManager,
          );
        }}
        type="button"
      >
        <FolderOpen size={16} />
        Show in folder
      </button>
    );
  }

  function csvZipRevealOrDownload(
    record: Pick<ExportRecord, "id" | "mode" | "status" | "output_path">,
    downloadLabel: string,
  ) {
    if (!isExportDownloadable(record)) {
      return null;
    }
    if (desktopShell) {
      return showInFolderButton(record.output_path);
    }
    return (
      <a
        className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-leaf px-4 py-2 font-medium text-white"
        href={exportDownloadUrl(projectId, record.id)}
      >
        <Download size={16} />
        {downloadLabel}
      </a>
    );
  }

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-muted">
          {exportSelectedCountLabel({ isLoading: statusCountsLoading, selectedCount })}
        </p>
        <h1 className="mt-1 text-3xl font-semibold">Export Selection</h1>
        {projectQuery.data?.root_path ? (
          <p className="mt-2 break-all text-sm text-muted">
            Exports folder: {projectExportRoot(projectQuery.data.root_path)}
          </p>
        ) : null}
        {nativeFs ? <div className="mt-2">{openExportFolderButton()}</div> : null}
      </div>
      <div className="grid gap-2 rounded border border-line bg-surface p-4">
        <h2 className="text-sm font-semibold">Statuses</h2>
        <div className="grid gap-2 sm:grid-cols-4">
          {EXPORT_STATUSES.map((status) => (
            <label
              className={`focus-within:ring-2 focus-within:ring-leaf flex items-center justify-between gap-3 rounded border border-line px-3 py-2 text-sm ${
                exportControlsDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
              }`}
              key={status}
            >
              <span className="flex items-center gap-2">
                <input
                  checked={statuses.includes(status)}
                  className="h-4 w-4 accent-leaf"
                  disabled={exportControlsDisabled}
                  onChange={() => toggleStatus(status)}
                  type="checkbox"
                />
                {status}
              </span>
              <span className="text-muted">
                {exportStatusCountLabel({ count: statusCounts[status], isLoading: statusCountsLoading })}
              </span>
            </label>
          ))}
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { mode: "csv" as Mode, label: "CSV", icon: FileSpreadsheet },
          { mode: "folder" as Mode, label: "Folder", icon: FolderOutput },
          { mode: "zip" as Mode, label: "ZIP", icon: FileArchive },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <button
              aria-pressed={mode === item.mode}
              className={`focus-ring flex min-h-24 items-center justify-center gap-3 rounded border px-4 font-medium disabled:cursor-not-allowed disabled:opacity-60 ${
                mode === item.mode ? "border-leaf bg-surface text-leaf" : "border-line bg-surface"
              }`}
              disabled={exportControlsDisabled}
              key={item.mode}
              onClick={() => setMode(item.mode)}
              type="button"
            >
              <Icon size={22} />
              {item.label}
            </button>
          );
        })}
      </div>
      <label
        className={`focus-within:ring-2 focus-within:ring-leaf flex max-w-xl items-start gap-3 rounded border border-line bg-surface px-3 py-2 text-sm ${
          exportControlsDisabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
        }`}
      >
        <input
          checked={includeXmp}
          className="mt-0.5 h-4 w-4 accent-leaf"
          disabled={exportControlsDisabled}
          onChange={(event) => setIncludeXmp(event.target.checked)}
          type="checkbox"
        />
        <span>
          <span className="font-medium">Write XMP sidecars</span>
          <span className="mt-1 block text-muted">
            Sidecars go next to folder copies and inside ZIP. They are never written beside originals. CSV already
            includes status and stars.
          </span>
        </span>
      </label>
      <button
        className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-mist disabled:opacity-50"
        disabled={Boolean(exportBlockMessage)}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <Download size={18} />}
        Export
      </button>
      {projectQuery.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{projectQuery.error.message}</p>
          <p className="text-muted">{exportLoadRecoveryMessage("project")}</p>
        </div>
      ) : null}
      {statusCountsQuery.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{statusCountsQuery.error.message}</p>
          <p className="text-muted">{exportLoadRecoveryMessage("statusCounts")}</p>
        </div>
      ) : null}
      {exportBlockMessage && !statusCountsQuery.isError ? (
        <p className={`text-sm ${!statuses.length ? "text-coral" : "text-muted"}`}>{exportBlockMessage}</p>
      ) : null}
      {preferenceMessage ? (
        <p className={`text-sm ${PREFERENCE_MESSAGE_CLASS[exportPreferenceMessageTone(preferenceMessage)]}`}>
          {preferenceMessage}
        </p>
      ) : null}
      {mutation.data ? (
        <div className="grid gap-3 rounded border border-line bg-surface p-4 text-sm">
          <p className="break-all text-leaf">
            {photoCountLabel(mutation.data.selected_count)} exported
            {mutation.data.mode === "folder" ? ` to ${mutation.data.output_path}` : "."}
          </p>
          <p className="text-muted">Statuses: {formatExportStatusSummary(mutation.data.statuses)}</p>
          {copyPathButton(mutation.data.output_path)}
          {mutation.data.mode === "folder" ? openExportFolderButton(mutation.data.output_path) : null}
          {csvZipRevealOrDownload(mutation.data, `Download ${mutation.data.mode.toUpperCase()}`)}
        </div>
      ) : null}
      {copyError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{copyError}</p>
          <p className="text-muted">{copy.exportCopyPathRecovery}</p>
        </div>
      ) : null}
      {mutation.isError ? (
        <div className="grid gap-1 text-sm">
          <p className="text-coral">{mutation.error.message}</p>
          <p className="text-muted">{exportActionRecoveryMessage("runExport")}</p>
        </div>
      ) : null}
      <div className="grid gap-3">
        <h2 className="text-sm font-semibold">Export History</h2>
        {exportsQuery.isLoading ? <p className="text-sm text-muted">Loading export history...</p> : null}
        {exportsQuery.isError ? (
          <div className="grid gap-1 text-sm">
            <p className="text-coral">{exportsQuery.error.message}</p>
            <p className="text-muted">{exportLoadRecoveryMessage("history")}</p>
          </div>
        ) : null}
        {exportsQuery.data?.length ? (
          <div className="grid gap-2">
            {exportsQuery.data.map((record) => {
              const recoveryMessage = exportRecoveryMessage(record.status);
              return (
                <div
                  className="grid gap-1 rounded border border-line bg-surface p-3 text-sm sm:grid-cols-[1fr_auto] sm:items-center"
                  key={record.id}
                >
                  <div>
                    <p className="font-medium">
                      {record.mode.toUpperCase()} · {photoCountLabel(record.selected_count)}
                      {record.include_xmp ? " · XMP" : ""}
                      <span
                        className={`ml-2 ${
                          record.status === "failed"
                            ? "text-coral"
                            : record.status === "running"
                              ? "text-leaf"
                              : "text-muted"
                        }`}
                      >
                        {formatExportRecordStatus(record.status, {
                          processed_count: record.processed_count,
                          total_count: record.total_count,
                        })}
                      </span>
                    </p>
                    <p className="text-muted">Statuses: {formatExportStatusSummary(record.statuses)}</p>
                    <p className="break-all text-muted">{record.output_path}</p>
                    {record.status === "failed" && record.error_message ? (
                      <p className="text-coral">{record.error_message}</p>
                    ) : null}
                    {recoveryMessage ? <p className="text-muted">{recoveryMessage}</p> : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {copyPathButton(record.output_path)}
                    {record.mode === "folder" ? openExportFolderButton(record.output_path) : null}
                    {csvZipRevealOrDownload(record, "Download")}
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}
        {canLoadMoreExports ? (
          <button
            className="focus-ring w-fit rounded border border-line bg-surface px-3 py-2 text-sm font-medium disabled:opacity-50"
            disabled={exportsQuery.isFetching}
            onClick={() => setExportLimit((current) => current + RECENT_EXPORT_LIMIT)}
          >
            {exportsQuery.isFetching ? "Loading..." : "Load more exports"}
          </button>
        ) : null}
        {!exportsQuery.isLoading && !exportsQuery.isError && !exportsQuery.data?.length ? (
          <p className="text-sm text-muted">{copy.exportHistoryEmptyDetail}</p>
        ) : null}
      </div>
    </section>
  );
}
