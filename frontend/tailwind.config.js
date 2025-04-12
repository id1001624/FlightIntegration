/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色調
        'base': '#FFFFFF',
        'background': '#F8F9FA',
        // 主強調色 - 旅程感
        'primary': {
          DEFAULT: '#005F73',
          'light': '#0A9396',
          'dark': '#033F4D',
        },
        // 次強調色 - 溫暖點綴
        'secondary': {
          DEFAULT: '#F4A261',
          'light': '#F8BC8A',
          'dark': '#E07A38',
        },
        // 功能色彩
        'success': '#38B000',
        'warning': '#FFB703',
        'danger': '#DC2F02',
        'info': '#219EBC',
        // 中性色
        'border': '#DEE2E6',
        // 文字顏色
        'text': {
          'primary': '#212529',
          'secondary': '#6C757D',
          'muted': '#ADB5BD',
        }
      },
      fontFamily: {
        'sans': ['Inter', 'Noto Sans TC', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 2px 4px rgba(0,0,0,0.05)',
        'card-hover': '0 4px 8px rgba(0,0,0,0.08)',
        'elevation-1': '0 1px 3px rgba(0,0,0,0.05)',
        'elevation-2': '0 4px 6px rgba(0,0,0,0.05)',
        'elevation-3': '0 10px 15px rgba(0,0,0,0.05)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-gentle': 'pulseGentle 2s infinite',
        'float': 'float 6s ease-in-out infinite',
        'journey-line': 'journeyLine 1.5s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseGentle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        journeyLine: {
          '0%': { width: '0%', opacity: '0.5' },
          '100%': { width: '100%', opacity: '1' },
        },
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
      },
      // 添加背景漸變
      backgroundImage: {
        'journey-gradient': 'linear-gradient(120deg, #005F73 0%, #0A9396 100%)',
        'warm-gradient': 'linear-gradient(120deg, #F4A261 0%, #E07A38 100%)',
      },
    },
  },
  plugins: [],
} 