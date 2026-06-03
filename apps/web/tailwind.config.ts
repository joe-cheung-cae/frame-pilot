import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#151515",
        mist: "#f5f7f8",
        line: "#d8dedc",
        leaf: "#2f6f5e",
        coral: "#bf5b45",
        gold: "#a77721",
      },
    },
  },
  plugins: [],
};

export default config;
