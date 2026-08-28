import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { HelpShortcuts } from "./HelpShortcuts";
import { desktopMenuHelpSection } from "@/lib/menuRoutes";

afterEach(() => {
  cleanup();
  delete window.__FRAMEPILOT_DESKTOP__;
});

describe("HelpShortcuts", () => {
  it("keeps culling keys on Help without desktop menu accelerators in the browser shell", () => {
    delete window.__FRAMEPILOT_DESKTOP__;
    render(<HelpShortcuts />);
    expect(screen.getByText("P")).toBeTruthy();
    expect(screen.getByText("Mark Pick")).toBeTruthy();
    expect(screen.queryByRole("heading", { name: desktopMenuHelpSection.title })).toBeNull();
    for (const shortcut of desktopMenuHelpSection.shortcuts) {
      expect(screen.queryByText(shortcut.keys)).toBeNull();
    }
  });

  it("documents Cmd/Ctrl menu accelerators on desktop Help", () => {
    window.__FRAMEPILOT_DESKTOP__ = true;
    render(<HelpShortcuts />);
    expect(screen.getByRole("heading", { name: desktopMenuHelpSection.title })).toBeTruthy();
    for (const shortcut of desktopMenuHelpSection.shortcuts) {
      expect(screen.getByText(shortcut.keys)).toBeTruthy();
      expect(screen.getByText(shortcut.action)).toBeTruthy();
    }
    expect(
      screen.getByText(
        "Desktop also lists native menu accelerators CmdOrCtrl+N, CmdOrCtrl+W, and CmdOrCtrl+Q.",
      ),
    ).toBeTruthy();
    expect(screen.getByText("P")).toBeTruthy();
    expect(screen.getByText("Mark Pick")).toBeTruthy();
  });
});
