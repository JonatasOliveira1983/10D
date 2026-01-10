import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
    plugins: [
        react(),
        VitePWA({
            registerType: 'autoUpdate',
            includeAssets: ['favicon.svg', 'logo10D.png', 'SoHoje.png'],
            manifest: {
                name: '10D Alerta - Trading',
                short_name: '10D',
                description: 'Advanced Trading Signal System',
                theme_color: '#0a0a0b',
                background_color: '#0a0a0b',
                display: 'standalone',
                icons: [
                    {
                        src: 'logo10D.png',
                        sizes: '192x192',
                        type: 'image/png'
                    },
                    {
                        src: 'logo10D.png',
                        sizes: '512x512',
                        type: 'image/png'
                    }
                ]
            }
        })
    ],
    server: {
        port: 3000,
        host: true,
        proxy: {
            '/api': {
                target: 'http://localhost:5001',
                changeOrigin: true
            }
        }
    }
})
