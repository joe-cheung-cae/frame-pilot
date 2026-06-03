"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ClipboardCopy, Download, FileArchive, FileSpreadsheet, FolderOutput, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, exportDownloadUrl } from "@/lib/api";
import {
  EXPORT_STATUSES,
  formatExportStatusSummary,
  isExportDownloadable,
  selectedPhotoCount,
  type ExportStatus,
} from "@/lib/exportSelection";
import { DEFAULT_EXPORT_STATUS_PREFERENCE, loadExportStatusPreference } from "@/lib/settings";

type Mode = "csv" | "folder" | "zip";

const RECENT_EXPORT_LIMIT = 50;

function projectExportRoot(rootPath: string) {
  return `${rootPath.replace(/[\\/]+$/, "")}/exports`;
}

function photoCountLabel(count: number) {
  return `${count} ${count === 1 ? "photo" : "photos"}`;
}

export function ExportPanel({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<Mode>("csv");
  const [statuses, setStatuses] = useState<ExportStatus[]>(DEFAULT_EXPORT_STATUS_PREFERENCE);
  const [exportLimit, setExportLimit] = useState(RECENT_EXPORT_LIMIT);
  const [copiedPath, setCopiedPath] = useState("");
  const [copyError, setCopyError] = useState("");
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
  });
  const statusCounts = statusCountsQuery.data ?? { Pick: 0, Maybe: 0, Reject: 0, Unreviewed: 0 };
  const selectedCount = selectedPhotoCount(statusCounts, statuses);
  const canLoadMoreExports = (exportsQuery.data?.length ?? 0) >= exportLimit;

  useEffect(() => {
    setStatuses(loadExportStatusPreference());
  }, []);

  const mutation = useMutation({
    mutationFn: () => {
      if (!statuses.length || selectedCount === 0) {
        throw new Error("Choose at least one non-empty status before exporting.");
      }
      return api.exportSelection(projectId, mode, statuses);
    },
    onSuccess: (record) => {
      queryClient.setQueryData(exportHistoryQueryKey, (current: unknown) =>
        Array.isArray(current) ? [record, ...current] : [record],
      );
    },
  });

  function toggleStatus(status: ExportStatus) {
    setStatuses((current) => {
      if (current.includes(status)) {
        return current.filter((item) => item !== status);
      }
      return [...current, status];
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

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">{photoCountLabel(selectedCount)} selected</p>
        <h1 className="mt-1 text-3xl font-semibold">Export Selection</h1>
        {projectQuery.data?.root_path ? (
          <p className="mt-2 break-all text-sm text-neutral-600">
            Exports folder: {projectExportRoot(projectQuery.data.root_path)}
          </p>
        ) : null}
      </div>
      <div className="grid gap-2 rounded border border-line bg-white p-4">
        <h2 className="text-sm font-semibold">Statuses</h2>
        <div className="grid gap-2 sm:grid-cols-4">
          {EXPORT_STATUSES.map((status) => (
            <label
              className="focus-within:ring-2 focus-within:ring-leaf flex cursor-pointer items-center justify-between gap-3 rounded border border-line px-3 py-2 text-sm"
              key={status}
            >
              <span className="flex items-center gap-2">
                <input
                  checked={statuses.includes(status)}
                  className="h-4 w-4 accent-leaf"
                  onChange={() => toggleStatus(status)}
                  type="checkbox"
                />
                {status}
              </span>
              <span className="text-neutral-600">{statusCounts[status]}</span>
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
              className={`focus-ring flex min-h-24 items-center justify-center gap-3 rounded border px-4 font-medium ${mode === item.mode ? "border-leaf bg-white text-leaf" : "border-line bg-white"}`}
              key={item.mode}
              onClick={() => setMode(item.mode)}
            >
              <Icon size={22} />
              {item.label}
            </button>
          );
        })}
      </div>
      <button
        className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-white disabled:opacity-50"
        disabled={mutation.isPending || statusCountsQuery.isLoading || !statuses.length || selectedCount === 0}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <Download size={18} />}
        Export
      </button>
      {!statuses.length ? <p className="text-sm text-coral">Choose at least one status to export.</p> : null}
      {projectQuery.isError ? <p className="text-sm text-coral">{projectQuery.error.message}</p> : null}
      {statusCountsQuery.isError ? <p className="text-sm text-coral">{statusCountsQuery.error.message}</p> : null}
      {statuses.length > 0 && selectedCount === 0 && !statusCountsQuery.isLoading && !statusCountsQuery.isError ? (
        <p className="text-sm text-neutral-600">No photos match the selected statuses.</p>
      ) : null}
      {mutation.data ? (
        <div className="grid gap-3 rounded border border-line bg-white p-4 text-sm">
          <p className="text-leaf">
            {photoCountLabel(mutation.data.selected_count)} exported
            {mutation.data.mode === "folder" ? ` to ${mutation.data.output_path}` : "."}
          </p>
          <p className="text-neutral-600">Statuses: {formatExportStatusSummary(mutation.data.statuses)}</p>
          {copyPathButton(mutation.data.output_path)}
          {isExportDownloadable(mutation.data) ? (
            <a
              className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-leaf px-4 py-2 font-medium text-white"
              href={exportDownloadUrl(projectId, mutation.data.id)}
            >
              <Download size={16} />
              Download {mutation.data.mode.toUpperCase()}
            </a>
          ) : null}
        </div>
      ) : null}
      {copyError ? <p className="text-sm text-coral">{copyError}</p> : null}
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
      <div className="grid gap-3">
        <h2 className="text-sm font-semibold">Export History</h2>
        {exportsQuery.isLoading ? (
          <p className="text-sm text-neutral-600">Loading export history...</p>
        ) : null}
        {exportsQuery.isError ? <p className="text-sm text-coral">{exportsQuery.error.message}</p> : null}
        {exportsQuery.data?.length ? (
          <div className="grid gap-2">
            {exportsQuery.data.map((record) => (
              <div
                className="grid gap-1 rounded border border-line bg-white p-3 text-sm sm:grid-cols-[1fr_auto] sm:items-center"
                key={record.id}
              >
                <div>
                  <p className="font-medium">
                    {record.mode.toUpperCase()} · {photoCountLabel(record.selected_count)}
                    <span className={record.status === "failed" ? "ml-2 text-coral" : "ml-2 text-neutral-500"}>
                      {record.status}
                    </span>
                  </p>
                  <p className="text-neutral-600">Statuses: {formatExportStatusSummary(record.statuses)}</p>
                  <p className="text-neutral-600">{record.output_path}</p>
                  {record.status === "failed" && record.error_message ? (
                    <p className="text-coral">{record.error_message}</p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  {copyPathButton(record.output_path)}
                  {isExportDownloadable(record) ? (
                    <a
                      className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-leaf px-3 py-2 font-medium text-white"
                      href={exportDownloadUrl(projectId, record.id)}
                    >
                      <Download size={16} />
                      Download
                    </a>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : null}
        {canLoadMoreExports ? (
          <button
            className="focus-ring w-fit rounded border border-line bg-white px-3 py-2 text-sm font-medium disabled:opacity-50"
            disabled={exportsQuery.isFetching}
            onClick={() => setExportLimit((current) => current + RECENT_EXPORT_LIMIT)}
          >
            {exportsQuery.isFetching ? "Loading..." : "Load more exports"}
          </button>
        ) : null}
        {!exportsQuery.isLoading && !exportsQuery.isError && !exportsQuery.data?.length ? (
          <p className="text-sm text-neutral-600">No exports yet.</p>
        ) : null}
      </div>
    </section>
  );
}
