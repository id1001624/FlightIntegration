import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  },
  // 性能優化配置
  build: {
    // 打包輸出配置
    outDir: 'dist',
    sourcemap: false, // 生產環境不生成sourcemap減少大小
    
    // 代碼分割配置
    rollupOptions: {
      output: {
        // 手動分割代碼塊
        manualChunks: {
          // Vue核心
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // HTTP請求庫
          'http-vendor': ['axios'],
          // UI工具庫 (如果有使用其他大型UI庫)
          // 'ui-vendor': ['element-plus', 'ant-design-vue']
        },
        // 優化文件命名
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)$/.test(assetInfo.name)) {
            return `media/[name]-[hash].${ext}`;
          }
          if (/\.(png|jpe?g|gif|svg|webp)$/.test(assetInfo.name)) {
            return `images/[name]-[hash].${ext}`;
          }
          if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name)) {
            return `fonts/[name]-[hash].${ext}`;
          }
          return `assets/[name]-[hash].${ext}`;
        }
      }
    },
    
    // 壓縮配置
    minify: 'terser',
    terserOptions: {
      compress: {
        // 移除console.log (生產環境)
        drop_console: true,
        drop_debugger: true,
        // 移除未使用的代碼
        dead_code: true,
        // 優化條件表達式
        conditionals: true
      },
      mangle: {
        // 混淆變數名稱
        safari10: true
      }
    },
    
    // 設置打包大小警告限制
    chunkSizeWarningLimit: 500, // 500KB
    
    // CSS代碼分割
    cssCodeSplit: true,
    
    // 資源內聯配置
    assetsInlineLimit: 4096 // 4KB以下的資源內聯為base64
  },
  
  // CSS相關優化
  css: {
    // 開發環境sourcemap
    devSourcemap: true,
    // PostCSS配置
    postcss: {
      plugins: [
        // 如果使用了PostCSS插件，可以在這裡配置
      ]
    }
  },
  
  // 優化依賴處理
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'axios'
    ],
    // 排除不需要預構建的依賴
    exclude: []
  }
}) 