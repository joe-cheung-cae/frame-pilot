import { projectIdFromPathname } from "./projectRouting.ts";

export const MENU_EVENT = "framepilot-menu";

export const NAVIGABLE_MENU_COMMANDS = ["new", "shortcuts", "import", "export", "process", "cull"] as const;

export type NavigableMenuCommand = (typeof NAVIGABLE_MENU_COMMANDS)[number];

export type MenuCommandResult = { type: "navigate"; href: string } | { type: "ignore" };

export const desktopMenuHelpSection = {
  title: "Desktop",
  shortcuts: [
    { keys: "CmdOrCtrl+N", action: "New project" },
    { keys: "CmdOrCtrl+W", action: "Close window" },
    { keys: "CmdOrCtrl+Q", action: "Quit" },
  ],
} as const;

const PROJECT_COMMANDS: Partial<Record<NavigableMenuCommand, "import" | "export" | "process" | "cull">> = {
  import: "import",
  export: "export",
  process: "process",
  cull: "cull",
};

export const MENU_WORKFLOW_QUERY = "workflow";

export function menuNeedsProjectHref(command: "import" | "export" | "process" | "cull"): string {
  return `/projects/new?${MENU_WORKFLOW_QUERY}=${command}`;
}

export function menuWorkflowPrompt(workflow: string | null | undefined): string {
  if (workflow === "import") {
    return "Create a project before opening Import.";
  }
  if (workflow === "export") {
    return "Create a project before opening Export.";
  }
  if (workflow === "process") {
    return "Create a project before opening Process.";
  }
  if (workflow === "cull") {
    return "Create a project before opening Culling.";
  }
  return "";
}

export function menuHrefForCommand(
  command: string,
  pathname: string,
  lastOpenedProjectId: string | null,
): string | null {
  if (command === "new") {
    return "/projects/new";
  }
  if (command === "shortcuts") {
    return "/help";
  }
  if (command !== "import" && command !== "export" && command !== "process" && command !== "cull") {
    return null;
  }
  const suffix = PROJECT_COMMANDS[command];
  if (!suffix) {
    return null;
  }
  const projectId = projectIdFromPathname(pathname) ?? lastOpenedProjectId;
  if (!projectId) {
    return menuNeedsProjectHref(command);
  }
  return `/projects/${projectId}/${suffix}`;
}

export function resolveMenuCommand(
  command: string,
  pathname: string,
  lastOpenedProjectId: string | null,
): MenuCommandResult {
  const href = menuHrefForCommand(command, pathname, lastOpenedProjectId);
  if (!href) {
    return { type: "ignore" };
  }
  return { type: "navigate", href };
}
