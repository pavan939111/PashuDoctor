import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sage: {
          50:  "#F4F8F4",
          100: "#E8F2E9",
          200: "#D0E6D2",
          300: "#A8CDB0",
          400: "#6FAE7A",
          500: "#3D7A52",   // primary
          600: "#2E5E3E",
          700: "#1F4229",
          800: "#132918",
          900: "#091509",
        },
        cream: {
          50:  "#FDFAF5",
          100: "#F9F5ED",
          200: "#F2EAD9",
        },
        earth: {
          400: "#C4973D",
          500: "#8B6914",
        }
      },
      fontFamily: {
        display: ["'Fraunces'", "Georgia", "serif"],
        body:    ["'DM Sans'", "system-ui", "sans-serif"],
        mono:    ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
        "4xl": "2rem",
      },
      animation: {
        "pulse-dot": "pulsedot 1.4s ease-in-out infinite",
        "shimmer":   "shimmer 1.5s infinite",
        "fade-up":   "fadeup 0.4s ease-out",
      },
      keyframes: {
        pulsedot: {
          "0%,60%,100%": {opacity:"0.3",transform:"scale(0.85)"},
          "30%": {opacity:"1",transform:"scale(1.1)"},
        },
        shimmer: {
          "0%":   {backgroundPosition:"200% 0"},
          "100%": {backgroundPosition:"-200% 0"},
        },
        fadeup: {
          "0%":   {opacity:"0",transform:"translateY(10px)"},
          "100%": {opacity:"1",transform:"translateY(0)"},
        }
      }
    }
  },
  plugins: [require("@tailwindcss/typography")],
};
export default config;
