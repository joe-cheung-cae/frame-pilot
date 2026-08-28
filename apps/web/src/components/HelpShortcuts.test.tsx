import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { HelpShortcuts } from "./HelpShortcuts";

afterEach(() => {
  cleanup();
  delete window.__FRAMEPILOT_DESKTOP__;
});

describe("HelpShortcuts", () => {
  it("keeps culling keys on Help in both shells", () => {
    render(<HelpShortcuts />);
    expect(screen.getByText("P")).toBeTruthy();
    expect(screen.getByText("Mark Pick")).toBeTruthy();
    expect(screen.queryByText("Desktop")).toBeNull();
    expect(screen.queryByText("CmdOrCtrl+N")).toBeNull();
  });

  it("documents Cmd/Ctrl menu accelerators on desktop Help", () => {
    window.__FRAMEPILOT_DESKTOP__ = true;
    render(<HelpShortcuts />);
    expect(screen.getByText("Desktop")).toBeTruthy();
    expect(screen.getByText("CmdOrCtrl+N")).toBeTruthy();
    expect(screen.getByText("New project")).toBeTruthy();
    expect(screen.getByText("CmdOrCtrl+Q")).toBeTruthy();
    expect(screen.getByText("P")).toBeTruthy();
    expect(screen.getByText("Mark Pick")).toBeTruthy();
  });
});
