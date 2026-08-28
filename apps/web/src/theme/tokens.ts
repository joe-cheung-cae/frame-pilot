export const colorHex = {
  ink: "#151515",
  mist: "#f5f7f8",
  line: "#d8dedc",
  leaf: "#2f6f5e",
  coral: "#bf5b45",
  gold: "#a77721",
  paper: "#ffffff",
} as const;

export const colors = {
  ink: "rgb(var(--fp-ink) / <alpha-value>)",
  mist: "rgb(var(--fp-mist) / <alpha-value>)",
  line: "rgb(var(--fp-line) / <alpha-value>)",
  leaf: "rgb(var(--fp-leaf) / <alpha-value>)",
  coral: "rgb(var(--fp-coral) / <alpha-value>)",
  gold: "rgb(var(--fp-gold) / <alpha-value>)",
  paper: "rgb(var(--fp-paper) / <alpha-value>)",
  surface: "rgb(var(--fp-surface) / <alpha-value>)",
  muted: "rgb(var(--fp-muted) / <alpha-value>)",
} as const;
