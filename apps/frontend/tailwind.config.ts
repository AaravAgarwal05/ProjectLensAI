import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        /* Brand — for landing page */
        brand: {
          DEFAULT: '#6366f1',
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
          dark: '#4f46e5',
        },
        'surface-card': '#111113',
        'surface-border': '#27272a',
        'surface-bg': '#09090b',

        /* M3 Dark palette (from designs) */
        primary: '#c0c1ff',
        'on-primary': '#1000a9',
        'primary-container': '#8083ff',
        'on-primary-container': '#0d0096',
        'primary-fixed': '#e1e0ff',
        'primary-fixed-dim': '#c0c1ff',
        'on-primary-fixed': '#07006c',
        'on-primary-fixed-variant': '#2f2ebe',

        secondary: '#ddb7ff',
        'on-secondary': '#490080',
        'secondary-container': '#6f00be',
        'on-secondary-container': '#d6a9ff',
        'secondary-fixed': '#f0dbff',
        'secondary-fixed-dim': '#ddb7ff',
        'on-secondary-fixed': '#2c0051',
        'on-secondary-fixed-variant': '#6900b3',

        tertiary: '#89ceff',
        'on-tertiary': '#00344d',
        'tertiary-container': '#009ada',
        'on-tertiary-container': '#002d43',
        'tertiary-fixed': '#c9e6ff',
        'tertiary-fixed-dim': '#89ceff',
        'on-tertiary-fixed': '#001e2f',
        'on-tertiary-fixed-variant': '#004c6e',

        error: '#ffb4ab',
        'on-error': '#690005',
        'error-container': '#93000a',
        'on-error-container': '#ffdad6',

        background: '#131315',
        'on-background': '#e5e1e4',

        surface: '#131315',
        'surface-dim': '#131315',
        'surface-bright': '#39393b',
        'surface-container-lowest': '#0e0e10',
        'surface-container-low': '#1c1b1d',
        'surface-container': '#201f22',
        'surface-container-high': '#2a2a2c',
        'surface-container-highest': '#353437',
        'surface-variant': '#353437',
        'on-surface': '#e5e1e4',
        'on-surface-variant': '#c7c4d7',

        outline: '#908fa0',
        'outline-variant': '#464554',

        'inverse-surface': '#e5e1e4',
        'inverse-on-surface': '#313032',
        'inverse-primary': '#494bd6',
        'surface-tint': '#c0c1ff',

        /* Legacy colors — kept for backward compat */
        accent: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
      },
      fontFamily: {
        display: ['Geist', 'sans-serif'],
        body: ['Geist', 'sans-serif'],
        headline: ['Geist', 'sans-serif'],
        label: ['JetBrains Mono', 'monospace'],
        code: ['JetBrains Mono', 'monospace'],
        sans: ['Geist', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        display: ['48px', { lineHeight: '56px', letterSpacing: '-0.04em', fontWeight: '700' }],
        'body-lg': ['16px', { lineHeight: '24px', letterSpacing: '0', fontWeight: '400' }],
        'body-md': ['14px', { lineHeight: '20px', letterSpacing: '0', fontWeight: '400' }],
        'headline-md': ['20px', { lineHeight: '28px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'headline-lg': ['32px', { lineHeight: '40px', letterSpacing: '-0.02em', fontWeight: '600' }],
        'label-md': ['12px', { lineHeight: '16px', letterSpacing: '0.02em', fontWeight: '500' }],
        'code-sm': ['12px', { lineHeight: '18px', fontWeight: '400' }],
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '32px',
        gutter: '16px',
        'margin-desktop': '32px',
        'margin-mobile': '16px',
        base: '4px',
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        lg: '0.25rem',
        xl: '0.5rem',
        full: '0.75rem',
      },
      animation: {
        'fade-in': 'fade-in 0.5s ease-out forwards',
        'fade-in-delay-1': 'fade-in 0.5s ease-out 0.1s forwards',
        'fade-in-delay-2': 'fade-in 0.5s ease-out 0.2s forwards',
        'fade-in-delay-3': 'fade-in 0.5s ease-out 0.3s forwards',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
