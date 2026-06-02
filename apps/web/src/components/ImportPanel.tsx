"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ChangeEvent, useState } from "react";
import { FileImage, Loader2, Play } from "lucide-react";
import { api } from "@/lib/api";

export function ImportPanel({ projectId }: { projectId: string }) {
  const [message, setMessage] = useState("");
  const [skipped, setSkipped] = useState<{ filename: string; reason: string }[]>([]);
  const queryClient = useQueryClient();
  const project = useQuery({ queryKey: ["project", projectId], queryFn: () => api.getProject(projectId) });
  const mutation = useMutation({
    mutationFn: (files: FileList) => api.importPhotos(projectId, files),
    onSuccess: async (result) => {
      setMessage(`${result.imported.length} images imported and previewed.`);
      setSkipped(result.skipped);
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  function onFiles(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files?.length) {
      mutation.mutate(event.target.files);
    }
  }

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">{project.data?.name ?? "Project"}</p>
        <h1 className="mt-1 text-3xl font-semibold">Import Images</h1>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="focus-within:ring-2 focus-within:ring-leaf grid min-h-56 cursor-pointer place-items-center rounded border border-dashed border-line bg-white p-8 text-center">
          <input className="sr-only" type="file" multiple accept="image/jpeg,image/png,image/webp" onChange={onFiles} />
          <span className="grid gap-3">
            <FileImage className="mx-auto text-leaf" size={34} />
            <span className="font-medium">Choose image files</span>
            <span className="text-sm text-neutral-600">JPEG, PNG, and WebP are supported.</span>
          </span>
        </label>
        <label className="focus-within:ring-2 focus-within:ring-leaf grid min-h-56 cursor-pointer place-items-center rounded border border-dashed border-line bg-white p-8 text-center">
          <input
            className="sr-only"
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            onChange={onFiles}
            {...{ webkitdirectory: "", directory: "" }}
          />
          <span className="grid gap-3">
            <FileImage className="mx-auto text-leaf" size={34} />
            <span className="font-medium">Choose a folder</span>
            <span className="text-sm text-neutral-600">Original files are copied into the local project folder.</span>
          </span>
        </label>
      </div>
      {mutation.isPending ? <p className="inline-flex items-center gap-2 text-sm"><Loader2 className="animate-spin" size={16} />Importing and generating previews...</p> : null}
      {message ? <p className="text-sm text-leaf">{message}</p> : null}
      {skipped.length ? (
        <div className="rounded border border-line bg-white p-3 text-sm text-neutral-700">
          <p className="font-medium text-coral">{skipped.length} files skipped.</p>
          <ul className="mt-2 grid gap-1">
            {skipped.slice(0, 5).map((item) => (
              <li key={`${item.filename}-${item.reason}`}>{item.filename}: {item.reason}</li>
            ))}
          </ul>
          {skipped.length > 5 ? <p className="mt-2 text-neutral-600">Only the first 5 skipped files are shown.</p> : null}
        </div>
      ) : null}
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
      <Link className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-4 py-3 font-medium text-white" href={`/projects/${projectId}/process`}>
        <Play size={18} />
        Process Project
      </Link>
    </section>
  );
}
