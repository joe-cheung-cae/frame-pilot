export const MENU_EVENT = "framepilot-menu";

export type MenuCommandId =
  | "new"
  | "open-data-folder"
  | "import"
  | "export"
  | "close"
  | "quit"
  | "undo"
  | "redo"
  | "cut"
  | "copy"
  | "paste"
  | "select_all"
  | "fullscreen"
  | "process"
  | "cull"
  | "shortcuts"
  | "about";

export type MenuItemSpec = {
  id: MenuCommandId;
  label: string;
  accelerator: string | null;
};

export const MENU_ITEMS: Record<"File" | "Edit" | "View" | "Project" | "Help", MenuItemSpec[]> = {
  File: [
    { id: "new", label: "New", accelerator: "CmdOrCtrl+N" },
    { id: "open-data-folder", label: "Open data folder", accelerator: null },
    { id: "import", label: "Import", accelerator: null },
    { id: "export", label: "Export", accelerator: null },
    { id: "close", label: "Close", accelerator: "CmdOrCtrl+W" },
    { id: "quit", label: "Quit", accelerator: "CmdOrCtrl+Q" },
  ],
  Edit: [
    { id: "undo", label: "Undo", accelerator: "CmdOrCtrl+Z" },
    { id: "redo", label: "Redo", accelerator: "CmdOrCtrl+Shift+Z" },
    { id: "cut", label: "Cut", accelerator: "CmdOrCtrl+X" },
    { id: "copy", label: "Copy", accelerator: "CmdOrCtrl+C" },
    { id: "paste", label: "Paste", accelerator: "CmdOrCtrl+V" },
    { id: "select_all", label: "Select All", accelerator: "CmdOrCtrl+A" },
  ],
  View: [{ id: "fullscreen", label: "Fullscreen", accelerator: null }],
  Project: [
    { id: "process", label: "Process", accelerator: null },
    { id: "cull", label: "Culling", accelerator: null },
  ],
  Help: [
    { id: "shortcuts", label: "Shortcuts", accelerator: null },
    { id: "about", label: "About", accelerator: null },
  ],
};

const PROJECT_COMMANDS: Partial<Record<MenuCommandId, "import" | "export" | "process" | "cull">> = {
  import: "import",
  export: "export",
  process: "process",
  cull: "cull",
};

export function projectIdFromPathname(pathname: string): string | null {
  const match = pathname.match(/^\/projects\/([^/]+)/);
  const segment = match?.[1];
  if (!segment || segment === "new") {
    return null;
  }
  return segment;
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
  const suffix = PROJECT_COMMANDS[command as MenuCommandId];
  if (!suffix) {
    return null;
  }
  const projectId = projectIdFromPathname(pathname) ?? lastOpenedProjectId;
  if (!projectId) {
    return null;
  }
  return `/projects/${projectId}/${suffix}`;
}
