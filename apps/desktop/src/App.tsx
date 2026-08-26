import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { MENU_EVENT, menuHrefForCommand } from "@/lib/menuRoutes";
import { useNavigator } from "@/lib/navigation";
import { loadLastOpenedProjectId } from "@/lib/recentProjects";
import { applyShellDataset } from "@/lib/shell";
import { AppRoutes } from "./router";

function NativeMenuListener() {
  const navigator = useNavigator();
  useEffect(() => {
    const onMenu = (event: Event) => {
      const command = (event as CustomEvent<string>).detail;
      if (typeof command !== "string") {
        return;
      }
      const href = menuHrefForCommand(command, window.location.pathname, loadLastOpenedProjectId());
      if (href) {
        navigator.push(href);
      }
    };
    window.addEventListener(MENU_EVENT, onMenu);
    return () => window.removeEventListener(MENU_EVENT, onMenu);
  }, [navigator]);
  return null;
}

export function App() {
  const [queryClient] = useState(() => new QueryClient());
  applyShellDataset();
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <NativeMenuListener />
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
