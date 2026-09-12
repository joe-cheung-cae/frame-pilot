import { listen } from "@tauri-apps/api/event";
import { resolveApiBase } from "../../../web/src/lib/apiBase.ts";
import { MENU_EVENT, resolveMenuCommand } from "../../../web/src/lib/menuRoutes.ts";

export { MENU_EVENT };

export const TAKE_MENU_COMMAND = "take_menu_command";
export const ALLOW_TAKE_MENU_COMMAND = "allow-take-menu-command";
export const SIDECAR_MENU_COMMAND_PATH = "/api/desktop/menu-command";
export const TAKE_MENU_COMMAND_INTERVAL_MS = 200;

export function menuCommandFromPayload(payload: unknown): string | null {
  if (typeof payload === "string") {
    return payload;
  }
  if (payload && typeof payload === "object" && "payload" in payload) {
    const nested = (payload as { payload: unknown }).payload;
    return typeof nested === "string" ? nested : null;
  }
  return null;
}

export function menuCommandFromSidecarPayload(payload: unknown): string | null {
  if (!payload || typeof payload !== "object" || !("command" in payload)) {
    return null;
  }
  const command = (payload as { command: unknown }).command;
  return typeof command === "string" && command.length > 0 ? command : null;
}

export async function takeSidecarMenuCommand(apiBase = resolveApiBase()): Promise<string | null> {
  const response = await fetch(`${apiBase}${SIDECAR_MENU_COMMAND_PATH}`, { cache: "no-store" });
  if (!response.ok) {
    return null;
  }
  return menuCommandFromSidecarPayload(await response.json());
}

export function hrefForNativeMenuCommand(
  command: unknown,
  pathname: string,
  lastOpenedProjectId: string | null,
): string | null {
  const normalized = menuCommandFromPayload(command);
  if (!normalized) {
    return null;
  }
  const result = resolveMenuCommand(normalized, pathname, lastOpenedProjectId);
  return result.type === "navigate" ? result.href : null;
}

export async function subscribeNativeMenu(
  onCommand: (command: unknown) => void,
): Promise<() => void> {
  return listen(MENU_EVENT, (event) => {
    onCommand(event.payload);
  });
}
