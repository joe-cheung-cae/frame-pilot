"use client";

import { useLayoutEffect } from "react";

import { MENU_EVENT, resolveMenuCommand } from "@/lib/menuRoutes";
import { useNavigator, usePathname } from "@/lib/navigation";
import { loadLastOpenedProjectId } from "@/lib/recentProjects";

type MenuWindow = Window & { __FRAMEPILOT_MENU_READY__?: boolean };

export function MenuCommandListener() {
  const navigator = useNavigator();
  const pathname = usePathname();

  useLayoutEffect(() => {
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

    const menuWindow = window as MenuWindow;
    menuWindow.__FRAMEPILOT_MENU_READY__ = true;
    window.addEventListener(MENU_EVENT, onMenu);
    return () => {
      menuWindow.__FRAMEPILOT_MENU_READY__ = false;
      window.removeEventListener(MENU_EVENT, onMenu);
    };
  }, [navigator, pathname]);

  return null;
}
