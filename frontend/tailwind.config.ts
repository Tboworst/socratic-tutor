import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#07080A", raised: "#101319", sunk: "#0B0D12", line: "#1E232C" },
        paper: "#E8EBF0",
        muted: { DEFAULT: "#8A93A3", dim: "#616A79" },
        volt: { DEFAULT: "#0A84FF", dim: "#0A5CB8" },
        good: "#3FCF8E",
        warn: "#E8B33F",
        crit: "#FF5C5C",
      },
      fontFamily: {
        display: ["Archivo", "Helvetica Neue", "Arial", "sans-serif"],
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
