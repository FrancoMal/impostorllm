/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'gemma': '#FF6B6B',
        'mistral': '#4ECDC4',
        'llama': '#45B7D1',
        'phi': '#96CEB4',
        'deepseek': '#DDA0DD',
        'human': '#FFD700',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
      },
    },
  },
  plugins: [],
}
