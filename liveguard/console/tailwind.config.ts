import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx,js,jsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui"],
      },
      colors: {
        brand: {
          50: "#f0f7ff",
          100: "#dbebff",
          200: "#b7d7ff",
          300: "#86bbff",
          400: "#4d95ff",
          500: "#1f6fff",
          600: "#0f52db",
          700: "#0c3fa5",
          800: "#0b2f79",
          900: "#0a2457",
        },
        severity: {
          p0: "#E4000F",
          p1: "#F97316",
          p2: "#F59E0B",
          info: "#10B981",
        },
        surface: {
          base: "#0B0F1A",
          elev1: "#111727",
          elev2: "#18203A",
          border: "#1F2B4C",
        },
      },
      boxShadow: {
        card: "0 4px 24px -8px rgba(10, 22, 48, 0.35)",
        glow: "0 0 40px -10px rgba(31, 111, 255, 0.45)",
      },
    },
  },
  plugins: [],
};
export default config;
