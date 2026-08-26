"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { hasActiveProcessingJob } from "@/lib/processingProgress";
import { loadLastOpenedProjectId } from "@/lib/recentProjects";
import { isDesktopShell } from "@/lib/shell";
import { jobLabel, projectLabel, resolveStatusBarProjectId, sidecarLabel, statusBarJob } from "@/lib/statusBarModel";

const HEALTH_POLL_MS = 5000;
const ACTIVE_POLL_MS = 1000;

export function StatusBar() {
  if (!isDesktopShell()) {
    return null;
  }
  return <DesktopStatusBar />;
}

function DesktopStatusBar() {
  const [pathname, setPathname] = useState(() => (typeof window === "undefined" ? "/" : window.location.pathname));

  useEffect(() => {
    const timer = window.setInterval(() => {
      setPathname(window.location.pathname);
    }, ACTIVE_POLL_MS);
    return () => window.clearInterval(timer);
  }, []);

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
    refetchInterval: (query) => (hasActiveProcessingJob(query.state.data) ? ACTIVE_POLL_MS : HEALTH_POLL_MS),
  });

  const connected = healthQuery.isError ? false : healthQuery.data ? healthQuery.data.status === "ok" : null;
  const job = statusBarJob(jobsQuery.data);

  return (
    <footer
      role="status"
      aria-label="Desktop status"
      className="sticky bottom-0 border-t border-line bg-white px-5 py-2 text-sm text-neutral-700"
    >
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-1">
        <span>{sidecarLabel(connected)}</span>
        <span>{projectLabel(projectQuery.data?.name)}</span>
        <span>{jobLabel(job)}</span>
      </div>
    </footer>
  );
}
