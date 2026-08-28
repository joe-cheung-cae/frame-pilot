import type { Config } from "tailwindcss";
import { colors } from "./src/theme/tokens";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors,
    },
  },
  plugins: [],
};

export default config;
