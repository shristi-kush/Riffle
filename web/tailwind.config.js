/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          1: "#0A0E17",
          2: "#141A24",
          3: "#1B2230",
        },
        text: {
          high: "#F5F7FA",
          med: "#A0AAB8",
          low: "#5C6675",
        },
        primary: {
          400: "#8E93F0",
          500: "#5B63E8",
          600: "#4A51D4",
        },
        cyan: {
          accent: "#32C6F0",
        },
        purple: {
          accent: "#A78BFA",
        },
        success: {
          DEFAULT: "#34D399",
        },
        danger: {
          DEFAULT: "#F87171",
        },
        hairline: "rgba(255,255,255,0.07)",
      },
      fontFamily: {
        sans: ["Outfit", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        h1: ["clamp(40px, 6vw, 64px)", { lineHeight: "1.06", letterSpacing: "-0.02em", fontWeight: "700" }],
        h2: ["36px", { lineHeight: "1.15", letterSpacing: "-0.015em", fontWeight: "700" }],
        h3: ["24px", { lineHeight: "1.25", letterSpacing: "-0.01em", fontWeight: "600" }],
        h4: ["18px", { lineHeight: "1.35", fontWeight: "600" }],
        body: ["16px", { lineHeight: "1.6" }],
        small: ["14px", { lineHeight: "1.55" }],
        label: ["12px", { lineHeight: "1.4", letterSpacing: "0.14em", fontWeight: "500" }],
      },
      backgroundImage: {
        signature: "linear-gradient(135deg, #32C6F0 0%, #6D7CF0 50%, #9B6DF0 100%)",
        "signature-soft":
          "linear-gradient(135deg, rgba(50,198,240,0.18) 0%, rgba(109,124,240,0.18) 50%, rgba(155,109,240,0.18) 100%)",
      },
      boxShadow: {
        glow: "0 0 40px -12px rgba(91, 99, 232, 0.55)",
        "glow-cyan": "0 0 36px -12px rgba(50, 198, 240, 0.5)",
        panel: "0 24px 60px -24px rgba(0, 0, 0, 0.75)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blink: {
          "0%, 80%, 100%": { opacity: "0.25" },
          "40%": { opacity: "1" },
        },
        "wave-bar": {
          "0%, 100%": { transform: "scaleY(0.35)" },
          "50%": { transform: "scaleY(1)" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.7" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out both",
        blink: "blink 1.4s infinite both",
        "wave-bar": "wave-bar 1.1s ease-in-out infinite",
        "pulse-ring": "pulse-ring 2s ease-out infinite",
        float: "float 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
