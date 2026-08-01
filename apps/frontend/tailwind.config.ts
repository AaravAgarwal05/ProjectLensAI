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

        /*
         * M3 palette — resolved at runtime via CSS custom properties
         * (see globals.css for theme values). Value = space-separated RGB,
         * e.g. 192 193 255, so opacity modifiers (bg-primary/20) work.
         */
        primary: 'rgb(var(--primary) / <alpha-value>)',
        'on-primary': 'rgb(var(--on-primary) / <alpha-value>)',
        'primary-container': 'rgb(var(--primary-container) / <alpha-value>)',
        'on-primary-container': 'rgb(var(--on-primary-container) / <alpha-value>)',
        'primary-fixed': 'rgb(var(--primary-fixed) / <alpha-value>)',
        'primary-fixed-dim': 'rgb(var(--primary-fixed-dim) / <alpha-value>)',
        'on-primary-fixed': 'rgb(var(--on-primary-fixed) / <alpha-value>)',
        'on-primary-fixed-variant': 'rgb(var(--on-primary-fixed-variant) / <alpha-value>)',

        secondary: 'rgb(var(--secondary) / <alpha-value>)',
        'on-secondary': 'rgb(var(--on-secondary) / <alpha-value>)',
        'secondary-container': 'rgb(var(--secondary-container) / <alpha-value>)',
        'on-secondary-container': 'rgb(var(--on-secondary-container) / <alpha-value>)',
        'secondary-fixed': 'rgb(var(--secondary-fixed) / <alpha-value>)',
        'secondary-fixed-dim': 'rgb(var(--secondary-fixed-dim) / <alpha-value>)',
        'on-secondary-fixed': 'rgb(var(--on-secondary-fixed) / <alpha-value>)',
        'on-secondary-fixed-variant': 'rgb(var(--on-secondary-fixed-variant) / <alpha-value>)',

        tertiary: 'rgb(var(--tertiary) / <alpha-value>)',
        'on-tertiary': 'rgb(var(--on-tertiary) / <alpha-value>)',
        'tertiary-container': 'rgb(var(--tertiary-container) / <alpha-value>)',
        'on-tertiary-container': 'rgb(var(--on-tertiary-container) / <alpha-value>)',
        'tertiary-fixed': 'rgb(var(--tertiary-fixed) / <alpha-value>)',
        'tertiary-fixed-dim': 'rgb(var(--tertiary-fixed-dim) / <alpha-value>)',
        'on-tertiary-fixed': 'rgb(var(--on-tertiary-fixed) / <alpha-value>)',
        'on-tertiary-fixed-variant': 'rgb(var(--on-tertiary-fixed-variant) / <alpha-value>)',

        error: 'rgb(var(--error) / <alpha-value>)',
        'on-error': 'rgb(var(--on-error) / <alpha-value>)',
        'error-container': 'rgb(var(--error-container) / <alpha-value>)',
        'on-error-container': 'rgb(var(--on-error-container) / <alpha-value>)',

        background: 'rgb(var(--background) / <alpha-value>)',
        'on-background': 'rgb(var(--on-background) / <alpha-value>)',

        surface: 'rgb(var(--surface) / <alpha-value>)',
        'surface-dim': 'rgb(var(--surface-dim) / <alpha-value>)',
        'surface-bright': 'rgb(var(--surface-bright) / <alpha-value>)',
        'surface-container-lowest': 'rgb(var(--surface-container-lowest) / <alpha-value>)',
        'surface-container-low': 'rgb(var(--surface-container-low) / <alpha-value>)',
        'surface-container': 'rgb(var(--surface-container) / <alpha-value>)',
        'surface-container-high': 'rgb(var(--surface-container-high) / <alpha-value>)',
        'surface-container-highest': 'rgb(var(--surface-container-highest) / <alpha-value>)',
        'surface-variant': 'rgb(var(--surface-variant) / <alpha-value>)',
        'on-surface': 'rgb(var(--on-surface) / <alpha-value>)',
        'on-surface-variant': 'rgb(var(--on-surface-variant) / <alpha-value>)',

        outline: 'rgb(var(--outline) / <alpha-value>)',
        'outline-variant': 'rgb(var(--outline-variant) / <alpha-value>)',

        'inverse-surface': 'rgb(var(--inverse-surface) / <alpha-value>)',
        'inverse-on-surface': 'rgb(var(--inverse-on-surface) / <alpha-value>)',
        'inverse-primary': 'rgb(var(--inverse-primary) / <alpha-value>)',
        'surface-tint': 'rgb(var(--surface-tint) / <alpha-value>)',

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
        logo: ['Fraunces', 'serif'],
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
