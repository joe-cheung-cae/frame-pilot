"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowRight, FolderOpen, Images, LayoutDashboard, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import {
  projectHasActiveImport,
  projectNextActionLabel,
  projectNextHref,
  projectProgressSummary,
  projectsHaveActiveImport,
} from "@/lib/projectRouting";

export function ProjectList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
    retry: false,
    refetchInterval: (query) => (projectsHaveActiveImport(query.state.data ?? []) ? 1000 : false),
  });

  if (isLoading) {
    return <Loader2 className="animate-spin text-leaf" />;
  }

  if (error) {
    return <p className="text-sm text-coral">Could not load projects: {error.message}</p>;
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

  return (
    <div className="grid gap-3">
      {data.map((project) => {
        const nextHref = projectNextHref(project);
        const activeImport = projectHasActiveImport(project);
        return (
          <article className="grid gap-3 rounded border border-line bg-white p-4" key={project.id}>
            <span className="flex items-center justify-between gap-4">
              <Link className="focus-ring font-medium text-ink hover:text-leaf" href={nextHref}>
                {project.name}
              </Link>
              <Images size={18} className="text-leaf" />
            </span>
            <span className="text-sm text-neutral-600">{projectProgressSummary(project)}</span>
            {activeImport ? (
              <span className="inline-flex w-fit rounded bg-mist px-2 py-1 text-xs font-medium text-leaf">
                Import updating
              </span>
            ) : null}
            <Link
              className="focus-ring inline-flex w-fit items-center gap-1 text-sm font-medium text-leaf"
              href={nextHref}
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
