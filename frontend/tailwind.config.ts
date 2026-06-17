import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0a0a0f",
        panel: "#14141c",
        accent: "#6ee7ff",
        pos: "#2ecc71",
        neu: "#94a3b8",
        neg: "#ef4444",
      },
    },
  },
  plugins: [],
};
export default config;
