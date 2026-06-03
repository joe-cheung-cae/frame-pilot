"use client";

import { useEffect } from "react";
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
    },
  });
  const startedJob = mutation.data;
  const jobQuery = useQuery({
    queryKey: ["job", projectId, startedJob?.id],
    queryFn: () => api.getJob(projectId, startedJob?.id ?? ""),
    enabled: Boolean(startedJob?.id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1000 : false;
    },
  });
  const job = jobQuery.data ?? startedJob;
  const progress = job ? Math.round(job.progress_percent) : 0;
  const hasImportedPhotos = Boolean(project.data?.total_images);
  const canOpenCulling = job?.status === "complete" || Boolean(project.data?.processed_images);
  const statusLabel = job?.status ? job.status[0].toUpperCase() + job.status.slice(1) : "Ready";
  const isProcessing = job?.status === "queued" || job?.status === "running" || mutation.isPending;

  useEffect(() => {
    if (job?.status !== "complete") {
      return;
    }
    void queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    void queryClient.invalidateQueries({ queryKey: ["projects"] });
    void queryClient.invalidateQueries({ queryKey: ["photos", projectId] });
    void queryClient.invalidateQueries({ queryKey: ["groups", projectId] });
  }, [job?.status, projectId, queryClient]);

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">{project.data?.name ?? "Project"}</p>
        <h1 className="mt-1 text-3xl font-semibold">Processing Status</h1>
      </div>
      <div className="rounded border border-line bg-white p-5">
        <div className="flex items-center justify-between gap-4">
          <span className="font-medium">{statusLabel}</span>
          <span className="text-sm text-neutral-600">
            {job
              ? `${job.processed_items} of ${job.total_items} photos · ${job.failed_items} failed · ${progress}%`
              : `${project.data?.processed_images ?? 0} of ${project.data?.total_images ?? 0} processed`}
          </span>
        </div>
        <p className="mt-2 text-sm text-neutral-700">
          {job?.current_step ?? "Run grouping and ranking when imports are ready."}
        </p>
        <div className="mt-4 h-2 rounded bg-mist">
          <div
            className={`h-2 rounded ${job?.status === "failed" ? "bg-coral" : "bg-leaf"}`}
            style={{ width: `${progress}%` }}
          />
        </div>
        {job?.status === "failed" ? (
          <p className="mt-3 text-sm text-coral">
            {job.error_message ?? "Processing failed. Review the imported files and try again."}
          </p>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          className="focus-ring inline-flex items-center gap-2 rounded bg-leaf px-4 py-3 font-medium text-white disabled:opacity-50"
          disabled={isProcessing || !hasImportedPhotos}
          onClick={() => mutation.mutate()}
        >
          {isProcessing ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
          Run Grouping and Ranking
        </button>
        {!hasImportedPhotos ? (
          <Link
            className="focus-ring inline-flex items-center gap-2 rounded border border-line bg-white px-4 py-3 font-medium"
            href={`/projects/${projectId}/import`}
          >
            <Upload size={18} />
            Import Images
          </Link>
        ) : null}
        {canOpenCulling ? (
          <Link
            className="focus-ring inline-flex items-center gap-2 rounded border border-line bg-white px-4 py-3 font-medium"
            href={`/projects/${projectId}/cull`}
          >
            <Rows3 size={18} />
            Open Culling Workspace
          </Link>
        ) : null}
      </div>
      {!hasImportedPhotos ? (
        <p className="text-sm text-neutral-600">
          Import JPEG, PNG, or WebP images before running grouping and ranking.
        </p>
      ) : null}
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
    </section>
  );
}
