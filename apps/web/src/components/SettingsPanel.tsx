"use client";

import { useQuery } from "@tanstack/react-query";
import { FolderOpen } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EXPORT_STATUSES, type ExportStatus } from "@/lib/exportSelection";
import { getNativeFs } from "@/lib/nativeFs";
import {
  DEFAULT_EXPORT_STATUS_PREFERENCE,
  exportPreferenceMessageTone,
  isOnlySelectedExportStatus,
  loadExportStatusPreference,
  toggleSavedExportStatusPreference,
} from "@/lib/settings";
import { isDesktopShell } from "@/lib/shell";

const PREFERENCE_MESSAGE_CLASS = {
  neutral: "text-muted",
  success: "text-leaf",
  warning: "text-coral",
} as const;

export function SettingsPanel() {
  const nativeFs = getNativeFs();
  const desktopShell = isDesktopShell();
  const [statuses, setStatuses] = useState<ExportStatus[]>(DEFAULT_EXPORT_STATUS_PREFERENCE);
  const [message, setMessage] = useState("");
  const metaQuery = useQuery({
    queryKey: ["meta"],
    queryFn: api.getMeta,
    retry: false,
  });

  useEffect(() => {
    setStatuses(loadExportStatusPreference());
  }, []);

  function toggleStatus(status: ExportStatus) {
    const result = toggleSavedExportStatusPreference(statuses, status);
    setStatuses(result.statuses);
    setMessage(result.message);
  }

  const dataDir = metaQuery.data?.data_dir?.trim() ?? "";
  const showOpenDataFolder = desktopShell && Boolean(nativeFs) && Boolean(dataDir);

  return (
    <section className="mx-auto grid max-w-3xl gap-6 px-5 py-8">
      <div className="grid gap-2">
        <p className="text-sm text-muted">Local preferences</p>
        <h1 className="text-3xl font-semibold">Settings</h1>
      </div>

      <div className="grid gap-4 rounded border border-line bg-surface p-5">
        <div>
          <h2 className="font-semibold">Data directory</h2>
          <p className="mt-1 text-sm text-muted">
            FramePilot stores local project data here. Changing this location is not available in this version.
          </p>
        </div>
        <p
          aria-label="Data directory"
          className="break-all rounded border border-line bg-mist px-3 py-2 text-sm"
        >
          {metaQuery.isError
            ? "Could not load the data directory."
            : dataDir || "Loading data directory…"}
        </p>
        {showOpenDataFolder ? (
          <button
            className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line px-3 py-2 font-medium"
            onClick={() => {
              if (!nativeFs) {
                return;
              }
              void nativeFs.revealInFileManager(dataDir);
            }}
            type="button"
          >
            <FolderOpen size={16} />
            Open data folder
          </button>
        ) : null}
      </div>

      <div className="grid gap-4 rounded border border-line bg-surface p-5">
        <div>
          <h2 className="font-semibold">Default export statuses</h2>
          <p className="mt-1 text-sm text-muted">Stored in this browser only.</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-4">
          {EXPORT_STATUSES.map((status) => {
            const isFinalSelectedStatus = isOnlySelectedExportStatus(statuses, status);
            return (
              <label
                className={`focus-within:ring-2 focus-within:ring-leaf flex items-center gap-2 rounded border border-line px-3 py-2 text-sm ${
                  isFinalSelectedStatus ? "cursor-not-allowed opacity-60" : "cursor-pointer"
                }`}
                key={status}
              >
                <input
                  checked={statuses.includes(status)}
                  className="h-4 w-4 accent-leaf disabled:cursor-not-allowed"
                  disabled={isFinalSelectedStatus}
                  onChange={() => toggleStatus(status)}
                  type="checkbox"
                />
                {status}
              </label>
            );
          })}
        </div>
        <p className="text-sm text-muted">At least one default status stays selected for future exports.</p>
        {message ? (
          <p className={`text-sm ${PREFERENCE_MESSAGE_CLASS[exportPreferenceMessageTone(message)]}`}>{message}</p>
        ) : null}
      </div>
    </section>
  );
}
