import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const raiz = (ruta) => fileURLToPath(new URL(ruta, import.meta.url))

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  build: {
    // Cinco páginas, sin enrutador del lado del cliente: FastAPI sirve
    // dist/index.html en / y dist/<página>/index.html en /<página>/.
    rollupOptions: {
      input: {
        inicio: raiz('./index.html'),
        identificar: raiz('./identificar/index.html'),
        catalogo: raiz('./catalogo/index.html'),
        creditos: raiz('./creditos/index.html'),
        registros: raiz('./registros/index.html'),
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './pruebas/preparacion.js',
    include: ['pruebas/**/*.test.{js,jsx}'],
  },
})
