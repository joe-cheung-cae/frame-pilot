"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, FileArchive, FileSpreadsheet, FolderOutput, Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import { countPhotosByStatus, EXPORT_STATUSES, selectedPhotoCount, type ExportStatus } from "@/lib/exportSelection";

type Mode = "csv" | "folder" | "zip";

export function ExportPanel({ projectId }: { projectId: string }) {
  const [mode, setMode] = useState<Mode>("csv");
  const [statuses, setStatuses] = useState<ExportStatus[]>(["Pick", "Maybe"]);
  const photosQuery = useQuery({ queryKey: ["photos", projectId], queryFn: () => api.listPhotos(projectId) });
  const statusCounts = useMemo(() => countPhotosByStatus(photosQuery.data ?? []), [photosQuery.data]);
  const selectedCount = selectedPhotoCount(statusCounts, statuses);
  const mutation = useMutation({ mutationFn: () => api.exportSelection(projectId, mode, statuses) });

  function toggleStatus(status: ExportStatus) {
    setStatuses((current) => {
      if (current.includes(status)) {
        return current.filter((item) => item !== status);
      }
      return [...current, status];
    });
  }

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">{selectedCount} selected photos</p>
        <h1 className="mt-1 text-3xl font-semibold">Export Selection</h1>
      </div>
      <div className="grid gap-2 rounded border border-line bg-white p-4">
        <h2 className="text-sm font-semibold">Statuses</h2>
        <div className="grid gap-2 sm:grid-cols-4">
          {EXPORT_STATUSES.map((status) => (
            <label className="focus-within:ring-2 focus-within:ring-leaf flex cursor-pointer items-center justify-between gap-3 rounded border border-line px-3 py-2 text-sm" key={status}>
              <span className="flex items-center gap-2">
                <input checked={statuses.includes(status)} className="h-4 w-4 accent-leaf" onChange={() => toggleStatus(status)} type="checkbox" />
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
        disabled={mutation.isPending || photosQuery.isLoading || !statuses.length || selectedCount === 0}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <Download size={18} />}
        Export
      </button>
      {!statuses.length ? <p className="text-sm text-coral">Choose at least one status to export.</p> : null}
      {statuses.length > 0 && selectedCount === 0 && !photosQuery.isLoading ? <p className="text-sm text-neutral-600">No photos match the selected statuses.</p> : null}
      {mutation.data ? <p className="text-sm text-leaf">{mutation.data.selected_count} photos exported to {mutation.data.output_path}</p> : null}
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
    </section>
  );
}
