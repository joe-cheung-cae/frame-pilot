"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FolderOpen, Images, LayoutDashboard, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Link } from "@/lib/navigation";
import {
  projectHasActiveImport,
  projectLoadRecoveryMessage,
  projectNextActionLabel,
  projectNextHref,
  projectProgressSummary,
  projectsHaveActiveImport,
} from "@/lib/projectRouting";
import { loadLastOpenedProjectId, orderProjectsByLastOpened, saveLastOpenedProjectId } from "@/lib/recentProjects";

export function ProjectList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
    retry: false,
    refetchInterval: (query) => (projectsHaveActiveImport(query.state.data ?? []) ? 1000 : false),
  });
  const [lastOpenedId, setLastOpenedId] = useState<string | null>(null);

  useEffect(() => {
    setLastOpenedId(loadLastOpenedProjectId());
  }, []);

  function rememberOpened(projectId: string) {
    setLastOpenedId(saveLastOpenedProjectId(projectId));
  }

  if (isLoading) {
    return <Loader2 className="animate-spin text-leaf" />;
  }

  if (error) {
    return (
      <div className="grid gap-1 text-sm">
        <p className="text-coral">Could not load projects: {error.message}</p>
        <p className="text-neutral-600">{projectLoadRecoveryMessage("list")}</p>
      </div>
    );
  }

  if (!data?.length) {
    return (
      <div className="grid gap-3 rounded border border-dashed border-line bg-mist p-4 text-sm">
        <p className="font-medium text-ink">No projects yet.</p>
        <p className="text-neutral-600">Create a local project before importing photos.</p>
        <Link
          className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-ink px-3 py-2 font-medium text-white"
          href="/projects/new"
        >
          <FolderOpen size={16} />
          Create Project
        </Link>
      </div>
    );
  }

  const projects = orderProjectsByLastOpened(data, lastOpenedId);

  return (
    <div className="grid gap-3">
      {projects.map((project) => {
        const nextHref = projectNextHref(project);
        const activeImport = projectHasActiveImport(project);
        const lastOpened = project.id === lastOpenedId;
        return (
          <article className="grid gap-3 rounded border border-line bg-white p-4" key={project.id}>
            <span className="flex items-center justify-between gap-4">
              <Link
                className="focus-ring font-medium text-ink hover:text-leaf"
                href={nextHref}
                onClick={() => rememberOpened(project.id)}
              >
                {project.name}
              </Link>
              <Images size={18} className="text-leaf" />
            </span>
            <span className="text-sm text-neutral-600">{projectProgressSummary(project)}</span>
            {lastOpened ? (
              <span className="inline-flex w-fit rounded bg-mist px-2 py-1 text-xs font-medium text-leaf">
                Last opened
              </span>
            ) : null}
            {activeImport ? (
              <span className="inline-flex w-fit rounded bg-mist px-2 py-1 text-xs font-medium text-leaf">
                Import updating
              </span>
            ) : null}
            <Link
              className="focus-ring inline-flex w-fit items-center gap-1 text-sm font-medium text-leaf"
              href={nextHref}
              onClick={() => rememberOpened(project.id)}
            >
              Next: {projectNextActionLabel(project)}
              <ArrowRight size={14} />
            </Link>
            <span className="grid gap-1 text-xs text-neutral-500">
              <span>Storage: Copy mode</span>
              <span className="break-all">Project data: {project.root_path}</span>
            </span>
            <Link
              className="focus-ring inline-flex w-fit items-center gap-2 rounded border border-line px-3 py-2 text-sm font-medium text-ink"
              href={`/projects/${project.id}`}
              onClick={() => rememberOpened(project.id)}
            >
              <LayoutDashboard size={16} />
              Dashboard
            </Link>
          </article>
        );
      })}
    </div>
  );
}
