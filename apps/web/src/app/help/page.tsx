import type { Metadata } from "next";
import { HelpShortcuts } from "@/components/HelpShortcuts";
import { Shell } from "@/components/Shell";

export const metadata: Metadata = {
  title: "Keyboard Shortcuts",
  description: "Review keyboard shortcuts for the FramePilot culling workspace",
};

export default function HelpPage() {
  return (
    <Shell>
      <HelpShortcuts />
    </Shell>
  );
}
