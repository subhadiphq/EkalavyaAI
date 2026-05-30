import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        caveat: ["var(--font-caveat)", "cursive"],
      },
      colors: {
        brand: { 50: "#eff6ff", 600: "#1e40af", 700: "#1d3a9e" },
      },
    },
  },
  plugins: [],
};

export default config;
