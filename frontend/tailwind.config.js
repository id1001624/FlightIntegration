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
        'base': '#F8F9FA',
        'base-white': '#FFFFFF',
        // 主強調色 - 旅程感
        'primary': {
          DEFAULT: '#2A9D8F',
          'light': '#40B5A7',
          'dark': '#1F756A',
        },
        // 次強調色 - 溫暖點綴
        'secondary': {
          DEFAULT: '#E9C46A',
          'light': '#F4D483',
          'dark': '#D4B154',
        },
        // 文字顏色
        'text': {
          'primary': '#212529',
          'secondary': '#6C757D',
        }
      },
      fontFamily: {
        'sans': ['Inter', 'Noto Sans TC', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 2px 4px rgba(0,0,0,0.05)',
        'card-hover': '0 4px 8px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
} 