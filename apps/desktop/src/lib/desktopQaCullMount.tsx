import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { MemoryRouter } from "react-router-dom";
import { invoke } from "@tauri-apps/api/core";
import { CullingWorkspace } from "@/components/CullingWorkspace";
import { Shell } from "@/components/Shell";

const HOST_ID = "framepilot-qa-cull-root";

export function mountCullWorkspace(projectId: string): void {
  if (typeof document === "undefined" || typeof document.body?.appendChild !== "function") {
    return;
  }
  let host = document.getElementById(HOST_ID);
  if (!host) {
    host = document.createElement("div");
    host.id = HOST_ID;
    host.setAttribute("data-framepilot-qa-cull", projectId);
    host.style.cssText = "position:fixed;inset:0;z-index:2147483647;background:#fff";
    document.body.appendChild(host);
  }
  const client = new QueryClient();
  const root = createRoot(host);
  void invoke("qa_write_evidence", {
    line: JSON.stringify({
      milestone: "cull_workspace",
      t: new Date().toISOString(),
      project_id: projectId,
      via: "root",
    }),
  }).catch(() => undefined);
  flushSync(() => {
    root.render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <Shell>
            <CullingWorkspace projectId={projectId} />
          </Shell>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  });
}
