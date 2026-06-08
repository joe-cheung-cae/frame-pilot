"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Download, Images, Loader2, Play, UploadCloud } from "lucide-react";
import { api } from "@/lib/api";
import {
  projectHasActiveImport,
  projectLoadRecoveryMessage,
  projectNextActionLabel,
  projectNextHref,
  projectProgressSummary,
  projectWorkflowStepHint,
  projectWorkflowStepHref,
} from "@/lib/projectRouting";

const workflowLinks = [
  { label: "Import", icon: UploadCloud, suffix: "import" },
  { label: "Process", icon: Play, suffix: "process" },
  { label: "Cull", icon: Images, suffix: "cull" },
  { label: "Export", icon: Download, suffix: "export" },
] as const;

export function ProjectDashboard({ projectId }: { projectId: string }) {
  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    retry: false,
    refetchInterval: (query) => (query.state.data && projectHasActiveImport(query.state.data) ? 1000 : false),
  });

  if (project.isLoading) {
    return (
      <section className="mx-auto grid max-w-5xl gap-6 px-5 py-8">
        <Loader2 className="animate-spin text-leaf" />
      </section>
    );
  }

  if (project.isError) {
    return (
      <section className="mx-auto grid max-w-5xl gap-6 px-5 py-8">
        <div className="grid gap-1 text-sm">
          <p className="text-coral">Could not load project details: {project.error.message}</p>
          <p className="text-neutral-600">{projectLoadRecoveryMessage("dashboard")}</p>
        </div>
      </section>
    );
  }

  if (!project.data) {
    return null;
  }

  const activeImport = projectHasActiveImport(project.data);

  return (
    <section className="mx-auto grid max-w-5xl gap-6 px-5 py-8">
      <div className="grid gap-2">
        <p className="text-sm text-neutral-600">Project dashboard</p>
        <h1 className="text-3xl font-semibold">{project.data.name}</h1>
        <p className="break-all text-sm text-neutral-600">Project data: {project.data.root_path}</p>
      </div>

      <div className="grid gap-3 rounded border border-line bg-white p-4 text-sm">
        <p className="font-medium">{projectProgressSummary(project.data)}</p>
        <Link
          className="focus-ring inline-flex w-fit items-center gap-2 rounded bg-leaf px-4 py-2 font-medium text-white"
          href={projectNextHref(project.data)}
        >
          {projectNextActionLabel(project.data)}
        </Link>
        {activeImport ? (
          <p className="text-sm text-neutral-600">
            Import is still running. Finish import progress before processing or culling.
          </p>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        {workflowLinks.map((item) => {
          const Icon = item.icon;
          const href = projectWorkflowStepHref(project.data, item.suffix);
          const hint = projectWorkflowStepHint(project.data, item.suffix);
          return (
            <Link
              className="focus-ring grid min-h-28 content-center justify-items-center gap-3 rounded border border-line bg-white p-4 text-center font-medium hover:border-leaf"
              href={href}
              key={item.suffix}
            >
              <Icon className="text-leaf" size={24} />
              <span>{item.label}</span>
              <span className="text-xs font-normal text-neutral-600">{hint}</span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
