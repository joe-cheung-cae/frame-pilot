import { listen } from "@tauri-apps/api/event";
import { MENU_EVENT, resolveMenuCommand } from "../../../web/src/lib/menuRoutes.ts";

export { MENU_EVENT };

export const TAKE_MENU_COMMAND = "take_menu_command";
export const ALLOW_TAKE_MENU_COMMAND = "allow-take-menu-command";
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
