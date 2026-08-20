function readGlobalWindow(): Window | undefined {
  return (globalThis as { window?: Window }).window;
}

function readGlobalDocument(): Document | undefined {
  return (globalThis as { document?: Document }).document;
}

export function isDesktopShell(): boolean {
  return readGlobalWindow()?.__FRAMEPILOT_DESKTOP__ === true;
}

export function applyShellDataset(): void {
  const root = readGlobalDocument()?.documentElement;
  if (!root) {
    return;
  }
  root.dataset.shell = isDesktopShell() ? "desktop" : "browser";
}
