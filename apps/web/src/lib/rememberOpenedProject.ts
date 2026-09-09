import { useEffect } from "react";

import { saveLastOpenedProjectId } from "./recentProjects.ts";

export function useRememberOpenedProject(projectId: string | null | undefined): void {
  useEffect(() => {
    if (projectId) {
      saveLastOpenedProjectId(projectId);
    }
  }, [projectId]);
}
