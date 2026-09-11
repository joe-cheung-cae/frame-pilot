import { listen } from "@tauri-apps/api/event";
import { MENU_EVENT, resolveMenuCommand } from "../../../web/src/lib/menuRoutes.ts";

export { MENU_EVENT };

export function hrefForNativeMenuCommand(
  command: unknown,
  pathname: string,
  lastOpenedProjectId: string | null,
): string | null {
  if (typeof command !== "string") {
    return null;
  }
  const result = resolveMenuCommand(command, pathname, lastOpenedProjectId);
  return result.type === "navigate" ? result.href : null;
}

export async function subscribeNativeMenu(
  onCommand: (command: unknown) => void,
): Promise<() => void> {
  return listen(MENU_EVENT, (event) => {
    onCommand(event.payload);
  });
}
