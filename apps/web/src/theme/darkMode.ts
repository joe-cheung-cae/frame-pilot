/**
 * Tailwind `dark:` applies only in the desktop shell when the OS theme is dark.
 * Browser (`[data-shell="browser"]`) stays light-only.
 */
export const desktopSystemDarkVariants: string[] = [
  '@media (prefers-color-scheme: dark) { &:is([data-shell="desktop"] *) }',
  '@media (prefers-color-scheme: dark) { &:is([data-shell="desktop"]) }',
];

export const desktopSystemDarkMode: ["variant", string[]] = [
  "variant",
  desktopSystemDarkVariants,
];
