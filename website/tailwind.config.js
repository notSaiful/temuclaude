/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Warm minimal palette — Anthropic-inspired
        bg: {
          primary: '#FAF8F5',
          secondary: '#F0EDE6',
          tertiary: '#E8E4DC',
          dark: '#1A1816',
        },
        text: {
          primary: '#1A1816',
          secondary: '#5E5B56',
          muted: '#8E8B85',
          inverse: '#FAF8F5',
        },
        accent: {
          primary: '#D97757',
          hover: '#C56547',
          light: '#F0D5C8',
          fig: '#C46686',
          olive: '#788C5D',
          amber: '#E8B547',
        },
        border: {
          subtle: 'rgba(26, 24, 22, 0.08)',
          default: 'rgba(26, 24, 22, 0.16)',
          strong: 'rgba(26, 24, 22, 0.24)',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Monaco', 'monospace'],
      },
      borderRadius: {
        sm: '8px',
        md: '16px',
        lg: '24px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(26, 24, 22, 0.04)',
        md: '0 4px 16px rgba(26, 24, 22, 0.08)',
        lg: '0 8px 32px rgba(26, 24, 22, 0.10)',
        glow: '0 0 24px rgba(217, 119, 87, 0.15)',
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.25, 1, 0.5, 1)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.25, 1, 0.5, 1)',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'draw-line': 'drawLine 1s ease-out forwards',
        'blink': 'blink 1s step-end infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        drawLine: {
          '0%': { strokeDashoffset: '1000' },
          '100%': { strokeDashoffset: '0' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}