import type { Config } from "tailwindcss";
import { desktopSystemDarkMode } from "../web/src/theme/darkMode";
import { colors } from "../web/src/theme/tokens";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}", "../web/src/**/*.{js,ts,jsx,tsx}"],
  darkMode: desktopSystemDarkMode,
  theme: {
    extend: {
      colors,
    },
  },
  plugins: [],
};

export default config;
