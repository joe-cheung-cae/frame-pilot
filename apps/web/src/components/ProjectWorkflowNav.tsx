"use client";

import { Link, usePathname } from "@/lib/navigation";
import {
  PROJECT_WORKFLOW_TABS,
  projectIdFromPathname,
  projectWorkflowStepFromPathname,
  projectWorkflowTabHref,
} from "@/lib/projectRouting";

export function ProjectWorkflowNav() {
  const pathname = usePathname();
  const projectId = projectIdFromPathname(pathname);
  if (!projectId) {
    return null;
  }
  const currentStep = projectWorkflowStepFromPathname(pathname);

  return (
    <div className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-5 py-2" role="tablist" aria-label="Project workflow">
        {PROJECT_WORKFLOW_TABS.map((tab) => {
          const selected = currentStep === tab.step;
          return (
            <Link
              aria-selected={selected}
              className={`focus-ring inline-flex min-h-10 shrink-0 items-center rounded px-3 text-sm font-medium ${
                selected ? "bg-ink text-mist" : "text-ink hover:bg-mist"
              }`}
              href={projectWorkflowTabHref(projectId, tab.step)}
              key={tab.step}
              role="tab"
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
