import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0b5fff",
        accent: "#00a3ad",
        neutral: "#101828",
        muted: "#667085",
      },
    },
  },
  plugins: [],
};

export default config;
