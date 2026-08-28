import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const push = vi.fn();

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  useSearchParams: () => new URLSearchParams("filter=Pick"),
  usePathname: () => "/projects/project-1/cull",
}));

import { Link, useNavigator, usePathname, useQueryParams } from "@/lib/navigation";

function PushProbe({ href }: { href: string }) {
  const navigator = useNavigator();
  return (
    <button type="button" onClick={() => navigator.push(href)}>
      Go
    </button>
  );
}

function QueryProbe({ name }: { name: string }) {
  const queryParams = useQueryParams();
  return <span>{queryParams.get(name) ?? ""}</span>;
}

function PathnameProbe() {
  return <span>{usePathname()}</span>;
}

describe("navigation adapter", () => {
  it("renders Link as an anchor with the given href", () => {
    render(<Link href="/help">Help</Link>);
    expect(screen.getByRole("link", { name: "Help" })).toHaveAttribute("href", "/help");
  });

  it("calls push with the expected href", () => {
    push.mockReset();
    render(<PushProbe href="/projects/project-1/export" />);
    fireEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(push).toHaveBeenCalledWith("/projects/project-1/export");
  });

  it("reads a query value from useQueryParams", () => {
    render(<QueryProbe name="filter" />);
    expect(screen.getByText("Pick")).toBeTruthy();
  });

  it("reads the current pathname from the adapter", () => {
    render(<PathnameProbe />);
    expect(screen.getByText("/projects/project-1/cull")).toBeTruthy();
  });

  it("keeps next/link and next/navigation out of shared components", () => {
    const componentsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../components");
    const sourceNames = fs
      .readdirSync(componentsDir)
      .filter((name) => /\.(ts|tsx)$/.test(name) && !name.includes(".test."));
    const offenders = sourceNames.filter((name) => {
      const source = fs.readFileSync(path.join(componentsDir, name), "utf8");
      return /from\s+["']next\/link["']/.test(source) || /from\s+["']next\/navigation["']/.test(source);
    });
    expect(offenders).toEqual([]);
  });
});
