import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "20px",
      screens: {
        sm: "640px",
        md: "768px",
        lg: "1024px",
        xl: "1400px", // Max container from wireframes
      },
    },
    extend: {
      colors: {
        // Base neutrals
        black: "#0d0d0d",
        white: "#ffffff",
        gray: {
          50: "#fafafa",
          100: "#f5f5f5",
          200: "#e5e5e5",
          300: "#dddddd",
          400: "#cccccc",
          500: "#999999",
          600: "#666666",
          700: "#333333",
          800: "#1a1a1a",
          900: "#0d0d0d",
        },
        // Semantic colors for chat
        blue: {
          light: "#e8f4ff",
          border: "#b3d9ff",
          dark: "#1e3a5f",
        },
        green: {
          light: "#d4edda",
          DEFAULT: "#28a745",
          dark: "#155724",
          neon: "#7dff9f",
        },
        yellow: {
          light: "#fffbf0",
          bg: "#fff3cd",
          border: "#ffc107",
          text: "#856404",
        },
        red: {
          light: "#f8d7da",
          bg: "#fff5f5",
          DEFAULT: "#dc3545",
          dark: "#721c24",
        },
        // shadcn/ui compatibility
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      spacing: {
        // Extends default 0-16 with wireframe-specific values
        18: "18px",
        20: "20px",
        22: "22px",
        24: "24px",
        28: "28px",
        32: "32px",
        36: "36px",
        40: "40px",
        44: "44px",
        56: "56px",
        280: "280px", // Sidebar width
        320: "320px", // Mobile width
        600: "600px", // Modal width
        640: "640px", // Command palette width
      },
      fontSize: {
        10: ["10px", { lineHeight: "1.4" }],
        11: ["11px", { lineHeight: "1.4" }],
        12: ["12px", { lineHeight: "1.4" }],
        13: ["13px", { lineHeight: "1.5" }],
        14: ["14px", { lineHeight: "1.5" }],
        16: ["16px", { lineHeight: "1.5" }],
        18: ["18px", { lineHeight: "1.4" }],
      },
      borderRadius: {
        3: "3px",
        4: "4px",
        6: "6px",
        8: "8px",
        12: "12px",
        18: "18px",
        20: "20px",
        24: "24px",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        card: "0 4px 12px rgba(0, 0, 0, 0.15)",
        modal: "0 20px 60px rgba(0, 0, 0, 0.3)",
        sidebar: "2px 0 8px rgba(0, 0, 0, 0.15)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        loading: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        spin: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        blink: {
          "50%": { opacity: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        loading: "loading 1.5s ease-in-out infinite",
        spin: "spin 1s linear infinite",
        blink: "blink 1s infinite",
      },
      maxWidth: {
        "container": "1400px",
        "modal": "600px",
        "palette": "640px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
