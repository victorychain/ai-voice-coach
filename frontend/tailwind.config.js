/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'system-ui', 'sans-serif'],
        display: ['Clash Display', 'system-ui', 'sans-serif'],
      },
      colors: {
        coral: {
          50: '#fff5f2',
          100: '#ffe8e1',
          200: '#ffd5c8',
          300: '#ffb5a0',
          400: '#ff8b6b',
          500: '#ff6b47',
          600: '#ed4a26',
          700: '#c73a1b',
          800: '#a3311b',
          900: '#862e1c',
        },
        midnight: {
          50: '#f4f6fb',
          100: '#e8ecf6',
          200: '#ccd6eb',
          300: '#9fb3d9',
          400: '#6b8bc3',
          500: '#486dab',
          600: '#375590',
          700: '#2d4575',
          800: '#283c62',
          900: '#0f172a',
          950: '#080c16',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'wave': 'wave 1.5s ease-in-out infinite',
      },
      keyframes: {
        wave: {
          '0%, 100%': { transform: 'scaleY(0.5)' },
          '50%': { transform: 'scaleY(1)' },
        }
      }
    },
  },
  plugins: [],
}

