import type { Config } from "tailwindcss";
import { desktopSystemDarkMode } from "./src/theme/darkMode";
import { colors } from "./src/theme/tokens";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: desktopSystemDarkMode,
  theme: {
    extend: {
      colors,
    },
  },
  plugins: [],
};

export default config;
