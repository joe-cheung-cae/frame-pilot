"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { jobsRefetchIntervalMs } from "@/lib/processingProgress";
import { loadLastOpenedProjectId } from "@/lib/recentProjects";
import { isDesktopShell } from "@/lib/shell";
import { jobLabel, projectLabel, resolveStatusBarProjectId, sidecarLabel, statusBarJob } from "@/lib/statusBarModel";

const HEALTH_POLL_MS = 5000;

export function StatusBar({ pathname = "/" }: { pathname?: string } = {}) {
  if (!isDesktopShell()) {
    return null;
  }
  return <DesktopStatusBar pathname={pathname} />;
}

function DesktopStatusBar({ pathname }: { pathname: string }) {
  const projectId = resolveStatusBarProjectId(pathname, loadLastOpenedProjectId());

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
    retry: false,
    refetchInterval: HEALTH_POLL_MS,
  });

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId ?? ""),
    enabled: Boolean(projectId),
    retry: false,
    refetchInterval: HEALTH_POLL_MS,
  });

  const jobsQuery = useQuery({
    queryKey: ["jobs", projectId],
    queryFn: () => api.listJobs(projectId ?? "", { limit: 10, offset: 0 }),
    enabled: Boolean(projectId),
    retry: false,
    refetchInterval: (query) => jobsRefetchIntervalMs(query.state.data),
  });

  const connected = healthQuery.isError ? false : healthQuery.data ? healthQuery.data.status === "ok" : null;
  const job = statusBarJob(jobsQuery.data);

  return (
    <footer
      role="status"
      aria-label="Desktop status"
      className="shrink-0 border-t border-line bg-surface px-5 py-2 text-sm text-muted"
    >
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-1">
        <span>{sidecarLabel(connected)}</span>
        <span>{projectLabel(projectQuery.data?.name)}</span>
        <span>{jobLabel(job)}</span>
      </div>
    </footer>
  );
}
