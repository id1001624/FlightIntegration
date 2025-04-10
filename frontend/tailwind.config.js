/** @type {import('tailwindcss').Config} */
module.exports = {
  purge: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {
      colors: {
        // 主色調
        'base': '#F8F9FA',
        'base-white': '#FFFFFF',
        // 主強調色 - 旅程感
        'primary': {
          DEFAULT: '#0ea5e9', // sky-500
          light: '#7dd3fc', // sky-300
          dark: '#0369a1', // sky-700
        },
        // 次強調色 - 溫暖點綴
        'secondary': {
          DEFAULT: '#6b7280', // gray-500
          light: '#9ca3af', // gray-400
          dark: '#4b5563', // gray-600
        },
        'accent': {
          DEFAULT: '#f59e0b', // amber-500
          light: '#fbbf24', // amber-400
          dark: '#d97706', // amber-600
        },
        // 文字顏色
        'text': {
          'primary': '#1f2937', // gray-800
          'secondary': '#6b7280', // gray-500
        }
      },
      fontFamily: {
        sans: ['Noto Sans TC', 'Inter', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
        lg: '16px', // Added for consistency
      },
      boxShadow: {
        'card': '0 4px 20px rgba(0, 0, 0, 0.05)',
        'card-hover': '0 8px 30px rgba(0, 0, 0, 0.1)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)', // Added for consistency
      },
      animation: {
        'pulse-gentle': 'pulse-gentle 2s infinite',
      },
      keyframes: {
        'pulse-gentle': {
          '0%, 100%': { transform: 'translateY(-1px) scale(1)' },
          '50%': { transform: 'translateY(-1px) scale(1.05)' },
        }
      }
    },
  },
  variants: {
    extend: {
      transform: ['hover', 'focus'],
      translate: ['hover', 'focus'],
      opacity: ['disabled'],
      cursor: ['disabled'],
      boxShadow: ['hover'], // Ensure hover variants are enabled for shadow
    },
  },
  plugins: [],
} 