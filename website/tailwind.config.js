/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark glassmorphic palette — Linear/Vercel-inspired
        bg: {
          primary: '#08080A',
          secondary: '#0F0F12',
          tertiary: '#1B1B1F',
          dark: '#030304',
        },
        text: {
          primary: '#F4F4F6',
          secondary: '#A1A1A6',
          muted: '#717178',
          inverse: '#08080A',
        },
        accent: {
          primary: '#E25822',
          hover: '#F26E3A',
          light: '#2A170F',
          fig: '#D87C9E',
          olive: '#8FA673',
          amber: '#F3C562',
        },
        border: {
          subtle: 'rgba(255, 255, 255, 0.05)',
          default: 'rgba(255, 255, 255, 0.1)',
          strong: 'rgba(255, 255, 255, 0.18)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', '-apple-system', 'system-ui', 'sans-serif'],
        serif: ['var(--font-serif)', 'Georgia', 'serif'],
        mono: ['var(--font-mono)', 'SF Mono', 'Monaco', 'monospace'],
      },
      borderRadius: {
        sm: '8px',
        md: '16px',
        lg: '24px',
      },
      boxShadow: {
        sm: '0px 0px 0px 1px rgba(26, 24, 22, 0.04)',
        md: '0px 0px 0px 1px rgba(26, 24, 22, 0.08), rgba(26, 24, 22, 0.05) 0px 4px 24px',
        lg: '0px 0px 0px 1px rgba(26, 24, 22, 0.12), rgba(26, 24, 22, 0.08) 0px 8px 32px',
        glow: '0 0 24px rgba(217, 119, 87, 0.15)',
        ring: '0px 0px 0px 1px rgba(26, 24, 22, 0.08)',
        'ring-hover': '0px 0px 0px 1px rgba(26, 24, 22, 0.16)',
        whisper: 'rgba(26, 24, 22, 0.05) 0px 4px 24px',
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.25, 1, 0.5, 1)',
        material: 'cubic-bezier(0.4, 0, 0.2, 1)',
        quad: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        cubic: 'cubic-bezier(0.215, 0.61, 0.355, 1)',
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