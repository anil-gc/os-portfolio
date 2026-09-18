import tailwindcss from '@tailwindcss/postcss';
import vinext from 'vinext';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    css: { postcss: { plugins: [tailwindcss()] } },
    plugins: [vinext()],
    server: {
      host: '127.0.0.1',
      port: 5173,
      proxy: {
        '/api': {
          target: env.DJANGO_ORIGIN || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/media': {
          target: env.DJANGO_ORIGIN || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
  };
});
