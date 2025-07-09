/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        // GemPlay color scheme
        'bg-primary': '#010b20',
        'bg-secondary': '#011941',
        'surface-sidebar': '#0f172a',
        'surface-card': '#081730',
        'surface-hover': '#1a1f3a',
        'accent-primary': '#23d364',
        'accent-secondary': '#23d3a7',
        'accent-dark': '#1ba351', // 15% darker green for buttons and backgrounds
        'accent-dark-secondary': '#1ba388', // 15% darker secondary green
        'text-primary': '#ffffff',
        'text-secondary': '#c2c2c2',
        'text-muted': '#888888',
        'border-primary': '#1d1d36',
        'border-secondary': '#2a2a4a',
        // Gem colors
        'gem-ruby': '#d63031',
        'gem-amber': '#ff6b35',
        'gem-topaz': '#ffcc02',
        'gem-emerald': '#00aa55',
        'gem-aquamarine': '#0099cc',
        'gem-sapphire': '#0044cc',
        'gem-magic': '#6622cc',
        // Status colors
        'success': '#00dd88',
        'warning': '#ffcc02',
        'error': '#d63031',
        'info': '#0099cc',
      },
      fontFamily: {
        'russo': ['Russo One', 'sans-serif'],
        'rajdhani': ['Rajdhani', 'sans-serif'],
        'roboto': ['Roboto', 'sans-serif'],
      },
      boxShadow: {
        'gem': '0 0 15px rgba(102, 34, 204, 0.4)',
        'glow-primary': '0 0 10px rgba(35, 211, 100, 0.3)',
        'glow-secondary': '0 0 10px rgba(35, 211, 167, 0.3)',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #010b20 0%, #011941 100%)',
        'gradient-accent': 'linear-gradient(135deg, #1ba351 0%, #1ba388 100%)', // Darker greens
        'gradient-accent-light': 'linear-gradient(135deg, #23d364 0%, #23d3a7 100%)', // Original for text
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      screens: {
        'xs': '360px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
    },
  },
  plugins: [],
};