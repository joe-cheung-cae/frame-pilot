import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DetachedPreviewPane } from "./DetachedPreviewPane";

afterEach(() => {
  cleanup();
});

describe("DetachedPreviewPane", () => {
  it("renders an empty pane when there is no active photo", () => {
    render(<DetachedPreviewPane />);
    expect(screen.getByLabelText("Detached preview")).toBeTruthy();
    expect(screen.getByText("No photo selected")).toBeTruthy();
    expect(screen.queryByText(/Projects/i)).toBeNull();
    expect(screen.queryByRole("navigation")).toBeNull();
  });
});
