"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowRight, Images, LayoutDashboard, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { projectNextActionLabel, projectNextHref } from "@/lib/projectRouting";

export function ProjectList() {
  const { data, isLoading, error } = useQuery({ queryKey: ["projects"], queryFn: api.listProjects, retry: false });

  if (isLoading) {
    return <Loader2 className="animate-spin text-leaf" />;
  }

  if (error) {
    return <p className="text-sm text-coral">Could not load projects: {error.message}</p>;
  }

  if (!data?.length) {
    return <p className="text-sm text-neutral-600">No projects yet.</p>;
  }

  return (
    <div className="grid gap-3">
      {data.map((project) => {
        const nextHref = projectNextHref(project);
        return (
          <article className="grid gap-3 rounded border border-line bg-white p-4" key={project.id}>
            <span className="flex items-center justify-between gap-4">
              <Link className="focus-ring font-medium text-ink hover:text-leaf" href={nextHref}>
                {project.name}
              </Link>
              <Images size={18} className="text-leaf" />
            </span>
            <span className="text-sm text-neutral-600">
              {project.processed_images} of {project.total_images} processed
            </span>
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
