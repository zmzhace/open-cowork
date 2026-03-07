/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        background: '#0a0a0a',
        surface: '#171717',
        primary: '#6366f1', // Indigo
        'primary-hover': '#4f46e5',
        border: '#262626',
        text: '#ededed',
        'text-muted': '#a3a3a3',
      }
    },
  },
  plugins: [],
}
