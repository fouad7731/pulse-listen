import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Charte Pulse by Coca-Cola
        cream: "#F7F1E8",
        brand: "#F40009",
        brandDark: "#C5000A",
        gold: "#D4AF37",
        ink: "#1A1A1A",
        ink2: "#2A2A2A",
        muted: "#6B6B6B",
        line: "#E5E5E5",
        // semantique sentiment
        pos: "#1f9d55",
        neu: "#6B6B6B",
        neg: "#F40009",
      },
    },
  },
  plugins: [],
};
export default config;
