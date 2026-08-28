"use client";

import { Camera, CircleHelp, FolderOpen, SlidersHorizontal } from "lucide-react";
import { Link, usePathname } from "@/lib/navigation";
import { isDesktopShell } from "@/lib/shell";

import { StatusBar } from "./StatusBar";

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const desktopShell = isDesktopShell();
  return (
    <main className={desktopShell ? "flex h-screen flex-col overflow-hidden bg-mist" : "min-h-screen bg-mist"}>
      <header className="shrink-0 border-b border-line bg-surface">
        <div className="mx-auto grid max-w-7xl gap-3 px-5 py-4 sm:flex sm:items-center sm:justify-between">
          <Link href="/" className="flex items-center gap-3 font-semibold text-ink">
            <span className="grid h-9 w-9 place-items-center rounded bg-leaf text-white">
              <Camera size={19} />
            </span>
            FramePilot
          </Link>
          <nav
            className="grid grid-cols-3 gap-2 sm:flex sm:flex-wrap sm:items-center sm:justify-end"
            aria-label="Primary"
          >
            <Link
              href="/help"
              className="focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded border border-line px-3 text-sm font-medium text-ink"
            >
              <CircleHelp size={16} />
              Help
            </Link>
            <Link
              href="/settings"
              className="focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded border border-line px-3 text-sm font-medium text-ink"
            >
              <SlidersHorizontal size={16} />
              Settings
            </Link>
            <Link
              href="/projects/new"
              className="focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded bg-ink px-3 text-sm font-medium text-mist"
            >
              <FolderOpen size={16} />
              New Project
            </Link>
          </nav>
        </div>
      </header>
      <div className={desktopShell ? "flex min-h-0 flex-1 flex-col overflow-auto" : undefined}>{children}</div>
      <StatusBar pathname={pathname} />
    </main>
  );
}
