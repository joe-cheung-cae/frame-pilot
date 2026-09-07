import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { MemoryRouter } from "react-router-dom";
import { CullingWorkspace } from "@/components/CullingWorkspace";
import { DetachedPreviewPane } from "@/components/DetachedPreviewPane";
import { isPreviewWindow } from "@/lib/detachedPreview";
import { MENU_EVENT, resolveMenuCommand } from "@/lib/menuRoutes";
import { useNavigator, usePathname } from "@/lib/navigation";
import { loadLastOpenedProjectId } from "@/lib/recentProjects";
import { applyShellDataset } from "@/lib/shell";
import { Shell } from "@/components/Shell";
import {
  DesktopQaRunner,
  setDesktopQaNavigate,
  setDesktopQaRoute,
  useDesktopQaCullProjectId,
} from "./lib/desktopQaRunner";
import { AppRoutes } from "./router";

const QA_NAVIGATE_EVENT = "framepilot-qa-navigate";

function NativeMenuListener() {
  const navigator = useNavigator();
  const pathname = usePathname();
  setDesktopQaNavigate((href) => navigator.push(href));
  setDesktopQaRoute(pathname);
  useEffect(() => {
    const onMenu = (event: Event) => {
      const command = (event as CustomEvent<string>).detail;
      if (typeof command !== "string") {
        return;
      }
      const result = resolveMenuCommand(command, pathname, loadLastOpenedProjectId());
      if (result.type === "navigate") {
        navigator.push(result.href);
      }
    };
    const onQaNavigate = (event: Event) => {
      const href = (event as CustomEvent<string>).detail;
      if (typeof href === "string" && href) {
        navigator.push(href);
      }
    };
    window.addEventListener(MENU_EVENT, onMenu);
    window.addEventListener(QA_NAVIGATE_EVENT, onQaNavigate);
    return () => {
      window.removeEventListener(MENU_EVENT, onMenu);
      window.removeEventListener(QA_NAVIGATE_EVENT, onQaNavigate);
    };
  }, [navigator, pathname]);
  return null;
}

function QaOrRoutes() {
  const projectId = useDesktopQaCullProjectId();
  if (projectId) {
    return (
      <Shell>
        <CullingWorkspace projectId={projectId} />
      </Shell>
    );
  }
  return <AppRoutes />;
}

export function App() {
  const [queryClient] = useState(() => new QueryClient());
  applyShellDataset();
  if (isPreviewWindow()) {
    return (
      <QueryClientProvider client={queryClient}>
        <DetachedPreviewPane />
      </QueryClientProvider>
    );
  }
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NativeMenuListener />
        <DesktopQaRunner />
        <QaOrRoutes />
      </MemoryRouter>
    </QueryClientProvider>
  );
}
