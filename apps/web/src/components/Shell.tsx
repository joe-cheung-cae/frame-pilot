import Link from "next/link";
import { Camera, FolderOpen } from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-mist">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <Link href="/" className="flex items-center gap-3 font-semibold text-ink">
            <span className="grid h-9 w-9 place-items-center rounded bg-leaf text-white">
              <Camera size={19} />
            </span>
            FramePilot
          </Link>
          <Link
            href="/projects/new"
            className="focus-ring inline-flex items-center gap-2 rounded bg-ink px-3 py-2 text-sm font-medium text-white"
          >
            <FolderOpen size={16} />
            New Project
          </Link>
        </div>
      </header>
      {children}
    </main>
  );
}
