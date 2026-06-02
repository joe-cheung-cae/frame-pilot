"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Loader2, Play, Rows3 } from "lucide-react";
import { api } from "@/lib/api";

export function ProcessingPanel({ projectId }: { projectId: string }) {
  const project = useQuery({ queryKey: ["project", projectId], queryFn: () => api.getProject(projectId) });
  const mutation = useMutation({ mutationFn: () => api.processProject(projectId) });
  const job = mutation.data;
  const progress = job?.total_items ? Math.round((job.processed_items / job.total_items) * 100) : 0;

  return (
    <section className="mx-auto grid max-w-4xl gap-6 px-5 py-8">
      <div>
        <p className="text-sm text-neutral-600">{project.data?.name ?? "Project"}</p>
        <h1 className="mt-1 text-3xl font-semibold">Processing Status</h1>
      </div>
      <div className="rounded border border-line bg-white p-5">
        <div className="flex items-center justify-between gap-4">
          <span className="font-medium">{job?.current_step ?? "Ready"}</span>
          <span className="text-sm text-neutral-600">{progress}%</span>
        </div>
        <div className="mt-4 h-2 rounded bg-mist">
          <div className="h-2 rounded bg-leaf" style={{ width: `${progress}%` }} />
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          className="focus-ring inline-flex items-center gap-2 rounded bg-leaf px-4 py-3 font-medium text-white disabled:opacity-50"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
          Run Grouping and Ranking
        </button>
        <Link className="focus-ring inline-flex items-center gap-2 rounded border border-line bg-white px-4 py-3 font-medium" href={`/projects/${projectId}/cull`}>
          <Rows3 size={18} />
          Open Culling Workspace
        </Link>
      </div>
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
    </section>
  );
}

