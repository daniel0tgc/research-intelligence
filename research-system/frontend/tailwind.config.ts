import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#6366f1',
        accent: '#22d3ee',
        background: '#0a0a0f',
        surface: '#12121a',
        elevated: '#1a1a2e',
        textPrimary: '#e2e8f0',
        textMuted: '#64748b',
        border: '#1e293b',
      },
      borderRadius: {
        card: '8px',
      },
    },
  },
  plugins: [],
}

export default config
