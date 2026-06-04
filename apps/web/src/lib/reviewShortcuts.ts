export type ReviewShortcutCommand =
  | { type: "move_photo"; delta: -1 | 1 }
  | { type: "move_group"; delta: -1 | 1 }
  | { type: "mark"; status: "Pick" | "Maybe" | "Reject" | "Unreviewed" }
  | { type: "rate"; rating: number }
  | { type: "toggle_large_preview" }
  | { type: "toggle_zoom" }
  | { type: "toggle_compare" }
  | { type: "cycle_group" }
  | { type: "focus_filters" }
  | { type: "export" };

export type ReviewShortcutHelpSection = {
  title: string;
  shortcuts: { keys: string; action: string }[];
};

export const REVIEW_SHORTCUT_HELP_SECTIONS: ReviewShortcutHelpSection[] = [
  {
    title: "Navigation",
    shortcuts: [
      { keys: "Left Arrow", action: "Previous photo" },
      { keys: "Right Arrow", action: "Next photo" },
      { keys: "Up Arrow", action: "Previous group" },
      { keys: "Down Arrow", action: "Next group" },
    ],
  },
  {
    title: "Review",
    shortcuts: [
      { keys: "P", action: "Mark Pick" },
      { keys: "M", action: "Mark Maybe" },
      { keys: "X", action: "Mark Reject" },
      { keys: "U", action: "Mark Unreviewed" },
      { keys: "1 to 5", action: "Set star rating" },
      { keys: "0", action: "Clear star rating" },
    ],
  },
  {
    title: "Workspace",
    shortcuts: [
      { keys: "Space", action: "Toggle large preview" },
      { keys: "Z", action: "Toggle zoom" },
      { keys: "C", action: "Toggle compare" },
      { keys: "G", action: "Cycle group selection" },
      { keys: "F", action: "Focus filter menu" },
      { keys: "E", action: "Open export" },
    ],
  },
];

export function reviewShortcutCommandForKey(key: string): ReviewShortcutCommand | null {
  if (key === "ArrowLeft") return { type: "move_photo", delta: -1 };
  if (key === "ArrowRight") return { type: "move_photo", delta: 1 };
  if (key === "ArrowUp") return { type: "move_group", delta: -1 };
  if (key === "ArrowDown") return { type: "move_group", delta: 1 };
  if (key === " ") return { type: "toggle_large_preview" };

  const normalizedKey = key.toLowerCase();
  if (normalizedKey === "p") return { type: "mark", status: "Pick" };
  if (normalizedKey === "m") return { type: "mark", status: "Maybe" };
  if (normalizedKey === "x") return { type: "mark", status: "Reject" };
  if (normalizedKey === "u") return { type: "mark", status: "Unreviewed" };
  if (normalizedKey === "z") return { type: "toggle_zoom" };
  if (normalizedKey === "c") return { type: "toggle_compare" };
  if (normalizedKey === "g") return { type: "cycle_group" };
  if (normalizedKey === "f") return { type: "focus_filters" };
  if (normalizedKey === "e") return { type: "export" };

  const numeric = Number(key);
  if (numeric === 0) return { type: "rate", rating: 0 };
  if (numeric >= 1 && numeric <= 5) return { type: "rate", rating: numeric };
  return null;
}

export function reviewShortcutNeedsPreventDefault(command: ReviewShortcutCommand): boolean {
  return command.type === "move_group" || command.type === "toggle_large_preview";
}
