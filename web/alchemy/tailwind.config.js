/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        warframe: {
          bg: '#1a1c23',
          card: '#22252e',
          accent: '#3d4455',
          gold: '#c5a059',
        },
      },
    },
  },
  plugins: [],
};
