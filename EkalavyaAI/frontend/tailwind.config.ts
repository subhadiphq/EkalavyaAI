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
        brand: { 
          bg: "#0F0B1E",
          nav: "#1A0F3C",
          purple: "#4C1D95",
          orange: "#F97316",
          gold: "#FBBF24",
          textLight: "#FFFFFF",
          textBody: "#E5E7EB",
        },
      },
      backgroundColor: {
        "card-dark": "rgba(255,255,255,0.05)",
      },
    },
  },
  plugins: [],
};

export default config;
