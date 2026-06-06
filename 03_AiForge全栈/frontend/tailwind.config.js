/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        dark: {
          900: "#1d1d1f",
          800: "#2c2c2e",
          700: "#3a3a3c",
          600: "#48484a",
          500: "#555556",
        },
        accent: {
          DEFAULT: "#0071e3",
          blue: "#0071e3",
          light: "#0077ed",
          dark: "#005bb5",
          muted: "rgba(0,113,227,0.25)",
        },
        surface: {
          DEFAULT: "#2c2c2e",
          raised: "#3a3a3c",
          overlay: "#48484a",
        },
        hairline: "rgba(255,255,255,0.08)",
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
        body: ["Inter", "Noto Sans SC", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(0,113,227,0.25)",
        "glow-lg": "0 0 40px rgba(0,113,227,0.3)",
        card: "0 2px 8px rgba(0,0,0,0.3)",
        elevated: "0 8px 32px rgba(0,0,0,0.4)",
      },
    },
  },
  plugins: [],
};
