"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Loader2, Play, Rows3, Upload } from "lucide-react";
import { api } from "@/lib/api";
import {
  activeJobOfType,
  activeProcessingJob,
  processingActionBlockMessage,
  processingFailureNotice,
  processingProgressPercent,
  processingProgressSummary,
  processingStatusLabel,
} from "@/lib/processingProgress";
import { PROCESSING_FAILURE_FILTER } from "@/lib/reviewFilters";

const RECENT_JOB_LIMIT = 50;

export function ProcessingPanel({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [jobLimit, setJobLimit] = useState(RECENT_JOB_LIMIT);
  const project = useQuery({ queryKey: ["project", projectId], queryFn: () => api.getProject(projectId), retry: false });
  const mutation = useMutation({
    mutationFn: () => api.processProject(projectId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      await queryClient.invalidateQueries({ queryKey: ["jobs", projectId] });
    },
  });
  const jobsQuery = useQuery({
    queryKey: ["jobs", projectId, jobLimit],
    queryFn: () => api.listJobs(projectId, { limit: jobLimit, offset: 0 }),
    retry: false,
  });
  const startedJob = mutation.data;
  const resumedJob = activeProcessingJob(jobsQuery.data);
  const activeImportJob = project.data?.active_import_job ?? activeJobOfType(jobsQuery.data, "import");
  const currentJobId = startedJob?.id ?? resumedJob?.id;
  const jobQuery = useQuery({
    queryKey: ["job", projectId, currentJobId],
    queryFn: () => api.getJob(projectId, currentJobId ?? ""),
    enabled: Boolean(currentJobId),
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1000 : false;
    },
  });
  const job = jobQuery.data ?? startedJob ?? resumedJob;
  const progress = processingProgressPercent(job);
  const hasImportedPhotos = Boolean(project.data?.total_images);
  const canOpenCulling = job?.status === "complete" || Boolean(project.data?.processed_images);
  const statusLabel = processingStatusLabel(job?.status);
  const isProcessing = job?.status === "queued" || job?.status === "running" || mutation.isPending;
  const isImportRunning = activeImportJob?.status === "queued" || activeImportJob?.status === "running";
  const processingActionLabel = job?.status === "failed" ? "Retry Grouping and Ranking" : "Run Grouping and Ranking";
  const processingBlockMessage = processingActionBlockMessage({ hasImportedPhotos, isImportRunning, isProcessing });
  const canLoadMoreJobs = (jobsQuery.data?.length ?? 0) >= jobLimit;
  const jobFailureNotice = processingFailureNotice(job);
  const processingFailuresHref = `/projects/${projectId}/cull?filter=${encodeURIComponent(PROCESSING_FAILURE_FILTER)}`;

  useEffect(() => {
    if (job?.status !== "complete") {
      return;
    }
    void queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    void queryClient.invalidateQueries({ queryKey: ["projects"] });
    void queryClient.invalidateQueries({ queryKey: ["photos", projectId] });
    void queryClient.invalidateQueries({ queryKey: ["groups", projectId] });
    void queryClient.invalidateQueries({ queryKey: ["jobs", projectId] });
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
            {processingProgressSummary(job, project.data)}
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
        {jobFailureNotice && job?.status !== "failed" ? (
          <div className="mt-3 grid gap-2 text-sm">
            <p className="text-coral">{jobFailureNotice}</p>
            <Link
              className="focus-ring w-fit rounded border border-line bg-white px-3 py-2 font-medium"
              href={processingFailuresHref}
            >
              Review processing failures
            </Link>
          </div>
        ) : null}
        {isImportRunning ? (
          <div className="mt-3 grid gap-2 text-sm">
            <p className="font-medium text-coral">
              Import is still running. Wait for previews and analysis to finish before processing.
            </p>
            <p className="text-neutral-700">
              {activeImportJob.current_step} · {processingProgressSummary(activeImportJob, project.data)}
            </p>
            <Link
              className="focus-ring w-fit rounded border border-line bg-white px-3 py-2 font-medium"
              href={`/projects/${projectId}/import`}
            >
              Back to Import Progress
            </Link>
          </div>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          className="focus-ring inline-flex items-center gap-2 rounded bg-leaf px-4 py-3 font-medium text-white disabled:opacity-50"
          disabled={Boolean(processingBlockMessage)}
          onClick={() => mutation.mutate()}
        >
          {isProcessing ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
          {processingActionLabel}
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
      {processingBlockMessage ? <p className="text-sm text-neutral-600">{processingBlockMessage}</p> : null}
      {project.isError ? <p className="text-sm text-coral">{project.error.message}</p> : null}
      {mutation.isError ? <p className="text-sm text-coral">{mutation.error.message}</p> : null}
      {jobQuery.isError ? (
        <p className="text-sm text-coral">Could not load processing job status: {jobQuery.error.message}</p>
      ) : null}
      <div className="grid gap-3">
        <h2 className="text-sm font-semibold">Job History</h2>
        {jobsQuery.isLoading ? <p className="text-sm text-neutral-600">Loading job history...</p> : null}
        {jobsQuery.isError ? <p className="text-sm text-coral">{jobsQuery.error.message}</p> : null}
        {jobsQuery.data?.length ? (
          <div className="grid gap-2">
            {jobsQuery.data.map((record) => {
              const recordFailureNotice = processingFailureNotice(record) ?? record.error_message;
              return (
                <div
                  className="grid gap-1 rounded border border-line bg-white p-3 text-sm sm:grid-cols-[1fr_auto] sm:items-center"
                  key={record.id}
                >
                  <div>
                    <p className="font-medium">
                      {record.job_type}
                      <span className={record.status === "failed" ? "ml-2 text-coral" : "ml-2 text-neutral-500"}>
                        {record.status}
                      </span>
                    </p>
                    <p className="text-neutral-600">{record.current_step}</p>
                    {recordFailureNotice ? <p className="text-coral">{recordFailureNotice}</p> : null}
                  </div>
                  <p className="text-neutral-600">{processingProgressSummary(record, project.data)}</p>
                </div>
              );
            })}
          </div>
        ) : null}
        {canLoadMoreJobs ? (
          <button
            className="focus-ring w-fit rounded border border-line bg-white px-3 py-2 text-sm font-medium disabled:opacity-50"
            disabled={jobsQuery.isFetching}
            onClick={() => setJobLimit((current) => current + RECENT_JOB_LIMIT)}
          >
            {jobsQuery.isFetching ? "Loading..." : "Load more jobs"}
          </button>
        ) : null}
        {!jobsQuery.isLoading && !jobsQuery.isError && !jobsQuery.data?.length ? (
          <p className="text-sm text-neutral-600">No jobs yet.</p>
        ) : null}
      </div>
    </section>
  );
}
