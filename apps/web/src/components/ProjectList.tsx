"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Images, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

export function ProjectList() {
  const { data, isLoading, error } = useQuery({ queryKey: ["projects"], queryFn: api.listProjects });

  if (isLoading) {
    return <Loader2 className="animate-spin text-leaf" />;
  }

  if (error) {
    return <p className="text-sm text-coral">Start the local API to load projects.</p>;
  }

  if (!data?.length) {
    return <p className="text-sm text-neutral-600">No projects yet.</p>;
  }

  return (
    <div className="grid gap-3">
      {data.map((project) => (
        <Link
          className="focus-ring grid gap-2 rounded border border-line bg-white p-4 transition hover:border-leaf"
          href={`/projects/${project.id}/cull`}
          key={project.id}
        >
          <span className="flex items-center justify-between gap-4">
            <span className="font-medium">{project.name}</span>
            <Images size={18} className="text-leaf" />
          </span>
          <span className="text-sm text-neutral-600">
            {project.processed_images} of {project.total_images} processed
          </span>
        </Link>
      ))}
    </div>
  );
}

