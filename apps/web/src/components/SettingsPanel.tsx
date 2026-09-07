"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderOpen } from "lucide-react";
import { useEffect, useState, type ChangeEvent } from "react";
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

export const DATA_DIR_CHANGE_CONFIRM =
  "This copies the current FramePilot data directory and rewrites stored paths inside it. Camera cards and other source folders are not moved or modified. Continue?";

export const CLEAR_DERIVATIVES_CONFIRM =
  "This deletes generated thumbnails and previews only. Original photos, ratings, picks, groups, and exports stay. The next import or process regenerates missing previews. Continue?";

export function formatCacheBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return "0 B";
  }
  if (bytes < 1024) {
    return `${Math.round(bytes)} B`;
  }
  const kb = bytes / 1024;
  if (kb < 1024) {
    return `${kb < 10 ? kb.toFixed(1) : Math.round(kb)} KB`;
  }
  const mb = kb / 1024;
  if (mb < 1024) {
    return `${mb < 10 ? mb.toFixed(1) : Math.round(mb)} MB`;
  }
  const gb = mb / 1024;
  return `${gb < 10 ? gb.toFixed(1) : Math.round(gb)} GB`;
}

function cacheSummary(bytes: number, fileCount: number, projectCount: number): string {
  const files = fileCount === 1 ? "1 file" : `${fileCount} files`;
  const projects = projectCount === 1 ? "1 project" : `${projectCount} projects`;
  return `${formatCacheBytes(bytes)} · ${files} · ${projects}`;
}

export function SettingsPanel() {
  const nativeFs = getNativeFs();
  const desktopShell = isDesktopShell();
  const queryClient = useQueryClient();
  const [statuses, setStatuses] = useState<ExportStatus[]>(DEFAULT_EXPORT_STATUS_PREFERENCE);
  const [message, setMessage] = useState("");
  const [dataDirMessage, setDataDirMessage] = useState("");
  const [changingDataDir, setChangingDataDir] = useState(false);
  const [importWorkers, setImportWorkers] = useState(1);
  const [cacheMessage, setCacheMessage] = useState("");
  const [clearingCache, setClearingCache] = useState(false);
  const metaQuery = useQuery({
    queryKey: ["meta"],
    queryFn: api.getMeta,
    retry: false,
  });
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: api.getSettings,
    retry: false,
  });
  const cacheQuery = useQuery({
    queryKey: ["cache"],
    queryFn: api.getCache,
    retry: false,
  });

  useEffect(() => {
    setStatuses(loadExportStatusPreference());
  }, []);

  useEffect(() => {
    const value = settingsQuery.data?.import_workers;
    if (value === 1 || value === 2 || value === 3 || value === 4) {
      setImportWorkers(value);
    }
  }, [settingsQuery.data]);

  function toggleStatus(status: ExportStatus) {
    const result = toggleSavedExportStatusPreference(statuses, status);
    setStatuses(result.statuses);
    setMessage(result.message);
  }

  function onImportWorkersChange(event: ChangeEvent<HTMLSelectElement>) {
    const value = Number(event.target.value);
    if (value !== 1 && value !== 2 && value !== 3 && value !== 4) {
      return;
    }
    setImportWorkers(value);
    void api.patchSettings({ import_workers: value });
  }

  const dataDir = metaQuery.data?.data_dir?.trim() ?? "";
  const showOpenDataFolder = desktopShell && Boolean(nativeFs) && Boolean(dataDir);
  const showChangeDataDir = showOpenDataFolder;
  const cacheFileCount = cacheQuery.data?.file_count ?? 0;
  const canClearCache = !clearingCache && !cacheQuery.isLoading && cacheFileCount > 0;

  async function onClearDerivatives() {
    if (!canClearCache) {
      return;
    }
    const confirmed = window.confirm(CLEAR_DERIVATIVES_CONFIRM);
    if (!confirmed) {
      return;
    }
    setCacheMessage("");
    setClearingCache(true);
    try {
      await api.clearDerivatives();
      await queryClient.invalidateQueries({ queryKey: ["cache"] });
      await queryClient.invalidateQueries({ queryKey: ["photos"] });
    } catch (error) {
      setCacheMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setClearingCache(false);
    }
  }

  async function onChangeDataDirectory() {
    if (!nativeFs || changingDataDir) {
      return;
    }
    setDataDirMessage("");
    setChangingDataDir(true);
    try {
      const picked = await nativeFs.pickDirectory();
      if (!picked) {
        return;
      }
      const registered = await api.registerDesktopProjectRoot(picked);
      const confirmed = window.confirm(DATA_DIR_CHANGE_CONFIRM);
      if (!confirmed) {
        return;
      }
      const result = await api.changeDesktopDataDir(registered.path);
      if (nativeFs.applyDataDirectory) {
        await nativeFs.applyDataDirectory(result.data_dir);
      }
      await queryClient.invalidateQueries({ queryKey: ["meta"] });
    } catch (error) {
      setDataDirMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setChangingDataDir(false);
    }
  }

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
            {showChangeDataDir
              ? "FramePilot stores local project data here. Changing the location copies this directory and rewrites stored paths inside it. Camera cards and other source folders are not moved or modified."
              : "FramePilot stores local project data here. Changing this location is available in the desktop app."}
          </p>
        </div>
        <p aria-label="Data directory" className="break-all rounded border border-line bg-mist px-3 py-2 text-sm">
          {metaQuery.isError ? "Could not load the data directory." : dataDir || "Loading data directory…"}
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
        {showChangeDataDir ? (
          <button
            className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line px-3 py-2 font-medium disabled:cursor-not-allowed disabled:opacity-50"
            disabled={changingDataDir}
            onClick={() => {
              void onChangeDataDirectory();
            }}
            type="button"
          >
            Change data directory
          </button>
        ) : null}
        {dataDirMessage ? <p className="text-sm text-coral">{dataDirMessage}</p> : null}
      </div>

      <div className="grid gap-4 rounded border border-line bg-surface p-5">
        <div>
          <h2 className="font-semibold">Import workers</h2>
          <p className="mt-1 text-sm text-muted">
            More workers can speed thumbnail and preview generation on large imports. Grouping and ranking stay one job
            per project. Originals stay unchanged. This value applies to the next import job.
          </p>
        </div>
        <label className="grid w-fit gap-2 text-sm">
          Import workers
          <select
            aria-label="Import workers"
            className="focus-ring rounded border border-line bg-mist px-3 py-2"
            onChange={onImportWorkersChange}
            value={importWorkers}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={4}>4</option>
          </select>
        </label>
      </div>

      <div className="grid gap-4 rounded border border-line bg-surface p-5">
        <div>
          <h2 className="font-semibold">Derivative cache</h2>
          <p className="mt-1 text-sm text-muted">
            Thumbnails and previews are generated copies. Clearing them does not touch originals, picks, ratings,
            groups, or exports. The next import or process regenerates missing previews.
          </p>
        </div>
        <p aria-label="Derivative cache size" className="rounded border border-line bg-mist px-3 py-2 text-sm">
          {cacheQuery.isError
            ? "Could not load cache size."
            : cacheQuery.data
              ? cacheSummary(
                  cacheQuery.data.derivative_bytes,
                  cacheQuery.data.file_count,
                  cacheQuery.data.project_count,
                )
              : "Loading cache size…"}
        </p>
        <button
          className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line px-3 py-2 font-medium disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!canClearCache}
          onClick={() => {
            void onClearDerivatives();
          }}
          type="button"
        >
          {clearingCache ? "Clearing…" : "Clear thumbnails and previews"}
        </button>
        {cacheMessage ? <p className="text-sm text-coral">{cacheMessage}</p> : null}
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
