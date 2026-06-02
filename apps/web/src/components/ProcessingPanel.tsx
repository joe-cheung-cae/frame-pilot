"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Loader2, Play, Rows3, Upload } from "lucide-react";
import { api } from "@/lib/api";

export function ProcessingPanel({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const project = useQuery({ queryKey: ["project", projectId], queryFn: () => api.getProject(projectId) });
  const mutation = useMutation({
    mutationFn: () => api.processProject(projectId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      await queryClient.invalidateQueries({ queryKey: ["photos", projectId] });
      await queryClient.invalidateQueries({ queryKey: ["groups", projectId] });
    },
  });
  const job = mutation.data;
  const progress = job?.total_items ? Math.round((job.processed_items / job.total_items) * 100) : 0;
  const hasImportedPhotos = Boolean(project.data?.total_images);
  const canOpenCulling = job?.status === "complete" || Boolean(project.data?.processed_images);

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">{project.data?.name ?? "Project"}</p>
        <h1 className="mt-1 text-3xl font-semibold">Processing Status</h1>
      </div>
      <div className="rounded border border-line bg-white p-5">
        <div className="flex items-center justify-between gap-4">
          <span className="font-medium">{job?.current_step ?? "Ready"}</span>
          <span className="text-sm text-neutral-600">
            {job ? `${job.processed_items} of ${job.total_items} photos · ${progress}%` : `${project.data?.processed_images ?? 0} of ${project.data?.total_images ?? 0} processed`}
          </span>
        </div>
        <div className="mt-4 h-2 rounded bg-mist">
          <div className={`h-2 rounded ${job?.status === "failed" ? "bg-coral" : "bg-leaf"}`} style={{ width: `${progress}%` }} />
        </div>
        {job?.status === "failed" ? (
          <p className="mt-3 text-sm text-coral">{job.error_message ?? "Processing failed. Review the imported files and try again."}</p>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          className="focus-ring inline-flex items-center gap-2 rounded bg-leaf px-4 py-3 font-medium text-white disabled:opacity-50"
          disabled={mutation.isPending || !hasImportedPhotos}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
          Run Grouping and Ranking
        </button>
        {!hasImportedPhotos ? (
          <Link className="focus-ring inline-flex items-center gap-2 rounded border border-line bg-white px-4 py-3 font-medium" href={`/projects/${projectId}/import`}>
            <Upload size={18} />
            Import Images
          </Link>
        ) : null}
        {canOpenCulling ? (
          <Link className="focus-ring inline-flex items-center gap-2 rounded border border-line bg-white px-4 py-3 font-medium" href={`/projects/${projectId}/cull`}>
            <Rows3 size={18} />
            Open Culling Workspace
          </Link>
        ) : null}
      </div>
      {!hasImportedPhotos ? <p className="text-sm text-neutral-600">Import JPEG, PNG, or WebP images before running grouping and ranking.</p> : null}
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
    </section>
  );
}
