/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { 900: '#16314A', 800: '#1F3A5F', 700: '#2A567E' },
        ink: '#15202B',
        slate: { 600: '#42566A', 500: '#76889A' },
        line: '#E4E9EF',
        paper: '#F4F7FA',
        accent: '#1F6FEB',
        urgent: '#C0392B',
        urgentBg: '#FBEDEB',
        standard: '#2E6DA4',
        good: '#1F7A3E',
        goodBg: '#E9F4ED',
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
