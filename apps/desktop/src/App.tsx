import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { MemoryRouter } from "react-router-dom";
import { CullingWorkspace } from "@/components/CullingWorkspace";
import { DetachedPreviewPane } from "@/components/DetachedPreviewPane";
import { isPreviewWindow } from "@/lib/detachedPreview";
import { MENU_EVENT } from "@/lib/menuRoutes";
import { useNavigator, usePathname } from "@/lib/navigation";
import { loadLastOpenedProjectId } from "@/lib/recentProjects";
import { applyShellDataset } from "@/lib/shell";
import { Shell } from "@/components/Shell";
import {
  DesktopQaRunner,
  setDesktopQaMountCull,
  setDesktopQaNavigate,
  setDesktopQaRoute,
  writeCullWorkspaceMounted,
} from "./lib/desktopQaRunner";
import {
  hrefForNativeMenuCommand,
  TAKE_MENU_COMMAND,
  TAKE_MENU_COMMAND_INTERVAL_MS,
} from "./lib/nativeMenu";
import { AppRoutes } from "./router";

const QA_NAVIGATE_EVENT = "framepilot-qa-navigate";

function NativeMenuListener() {
  const navigator = useNavigator();
  const pathname = usePathname();
  const navigatorRef = useRef(navigator);
  const pathnameRef = useRef(pathname);
  navigatorRef.current = navigator;
  pathnameRef.current = pathname;
  setDesktopQaNavigate((href) => navigator.push(href));
  setDesktopQaRoute(pathname);
  useEffect(() => {
    const onQaNavigate = (event: Event) => {
      const href = (event as CustomEvent<string>).detail;
      if (typeof href === "string" && href) {
        navigatorRef.current.push(href);
      }
    };
    window.addEventListener(QA_NAVIGATE_EVENT, onQaNavigate);
    return () => {
      window.removeEventListener(QA_NAVIGATE_EVENT, onQaNavigate);
    };
  }, []);
  useEffect(() => {
    let disposed = false;
    let unlisten: (() => void) | undefined;
    const applyCommand = (payload: unknown) => {
      const href = hrefForNativeMenuCommand(
        payload,
        pathnameRef.current,
        loadLastOpenedProjectId(),
      );
      if (href) {
        navigatorRef.current.push(href);
      }
    };
    void listen<string>(MENU_EVENT, (event) => {
      applyCommand(event.payload);
    })
      .then((stop) => {
        if (disposed) {
          stop();
          return;
        }
        unlisten = stop;
      })
      .catch((error: unknown) => {
        console.error("FramePilot native menu listen failed", error);
      });
    const poll = window.setInterval(() => {
      void invoke<string | null>(TAKE_MENU_COMMAND)
        .then((command) => {
          if (!disposed && command) {
            applyCommand(command);
          }
        })
        .catch((error: unknown) => {
          console.error("FramePilot native menu take failed", error);
        });
    }, TAKE_MENU_COMMAND_INTERVAL_MS);
    return () => {
      disposed = true;
      window.clearInterval(poll);
      unlisten?.();
    };
  }, []);
  return null;
}

function CullOverlay() {
  const [projectId, setProjectId] = useState<string | null>(null);
  setDesktopQaMountCull((id) => {
    try {
      flushSync(() => {
        setProjectId(id);
      });
    } catch {
      setProjectId(id);
    }
  });
  if (!projectId) {
    return <AppRoutes />;
  }
  writeCullWorkspaceMounted(projectId);
  return (
    <Shell>
      <CullingWorkspace projectId={projectId} />
    </Shell>
  );
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
        <CullOverlay />
      </MemoryRouter>
    </QueryClientProvider>
  );
}
