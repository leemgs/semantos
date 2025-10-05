import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 프론트는 정적 서빙만; gRPC-Web은 Nginx에서 프록시 처리
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: 'dist',
    sourcemap: false
  },
  server: {
    port: 5173,
    strictPort: true
  }
})

