/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // 自定义颜色主题——法律/合同系统的专业配色
      colors: {
        primary: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        risk: {
          high:   "#ef4444",  // 红色——高风险
          medium: "#f59e0b",  // 黄色——中风险
          low:    "#22c55e",  // 绿色——低风险
        },
      },
    },
  },
  plugins: [],
};
