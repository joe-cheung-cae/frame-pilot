"use client";

import { useEffect } from "react";

import { MENU_EVENT, resolveMenuCommand } from "@/lib/menuRoutes";
import { useNavigator, usePathname } from "@/lib/navigation";
import { loadLastOpenedProjectId } from "@/lib/recentProjects";

export function MenuCommandListener() {
  const navigator = useNavigator();
  const pathname = usePathname();

  useEffect(() => {
    function onMenu(event: Event) {
      const command = (event as CustomEvent<string>).detail;
      if (typeof command !== "string") {
        return;
      }
      const result = resolveMenuCommand(command, pathname, loadLastOpenedProjectId());
      if (result.type === "navigate") {
        navigator.push(result.href);
      }
    }

    window.addEventListener(MENU_EVENT, onMenu);
    return () => {
      window.removeEventListener(MENU_EVENT, onMenu);
    };
  }, [navigator, pathname]);

  return null;
}
