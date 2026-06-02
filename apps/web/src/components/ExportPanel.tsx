"use client";

import { useMutation } from "@tanstack/react-query";
import { Download, FileArchive, FileSpreadsheet, FolderOutput, Loader2 } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";

type Mode = "csv" | "folder" | "zip";

export function ExportPanel({ projectId }: { projectId: string }) {
  const [mode, setMode] = useState<Mode>("csv");
  const mutation = useMutation({ mutationFn: () => api.exportSelection(projectId, mode, ["Pick", "Maybe"]) });

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">Picks and Maybes</p>
        <h1 className="mt-1 text-3xl font-semibold">Export Selection</h1>
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
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <Download size={18} />}
        Export
      </button>
      {mutation.data ? <p className="text-sm text-leaf">Export written to {mutation.data.output_path}</p> : null}
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
    </section>
  );
}

