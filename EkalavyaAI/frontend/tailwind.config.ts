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
          "purple-light": "#6B3FA0",
          orange: "#F97316",
          "orange-light": "#FB923C",
          gold: "#FBBF24",
          textLight: "#FFFFFF",
          textBody: "#E5E7EB",
          textMuted: "#9CA3AF",
        },
      },
      backgroundColor: {
        "card-dark": "rgba(255,255,255,0.05)",
        "card-dark-hover": "rgba(255,255,255,0.08)",
        "input-dark": "#1E1535",
        "glass": "rgba(255,255,255,0.05)",
      },
      backdropBlur: {
        xs: "2px",
      },
      borderColor: {
        "glass": "rgba(255,255,255,0.1)",
      },
      boxShadow: {
        "purple-glow": "0 0 30px rgba(76, 29, 149, 0.3)",
        "orange-glow": "0 0 30px rgba(249, 115, 22, 0.3)",
        "glass": "0 8px 32px rgba(0, 0, 0, 0.3)",
      },
      keyframes: {
        "slide-in-right": {
          "0%": { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { transform: "translateY(30px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "bounce-soft": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "wave": {
          "0%, 100%": { transform: "rotate(0deg)" },
          "10%": { transform: "rotate(14deg)" },
          "20%": { transform: "rotate(-8deg)" },
          "30%": { transform: "rotate(14deg)" },
          "40%": { transform: "rotate(-4deg)" },
          "50%": { transform: "rotate(10deg)" },
          "60%": { transform: "rotate(0deg)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 10px rgba(249, 115, 22, 0)" },
          "50%": { boxShadow: "0 0 20px rgba(249, 115, 22, 0.5)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        "typewriter": {
          "0%": { width: "0" },
          "100%": { width: "100%" },
        },
        "blink": {
          "0%, 49%": { opacity: "1" },
          "50%, 100%": { opacity: "0" },
        },
        "dots": {
          "0%, 20%": { content: "'.'", opacity: "0.3" },
          "40%": { content: "'..'", opacity: "0.6" },
          "60%, 100%": { content: "'...'", opacity: "1" },
        },
      },
      animation: {
        "slide-in-right": "slide-in-right 300ms ease-out",
        "fade-in": "fade-in 400ms ease-out",
        "slide-up": "slide-up 500ms ease-out",
        "bounce-soft": "bounce-soft 2s infinite",
        "float": "float 3s ease-in-out infinite",
        "wave": "wave 600ms ease-in-out",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "shimmer": "shimmer 2s infinite",
        "typewriter": "typewriter 1.5s steps(40, end)",
        "blink": "blink 0.7s infinite",
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
