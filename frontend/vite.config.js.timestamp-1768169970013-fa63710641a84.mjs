// vite.config.js
import { defineConfig } from "file:///C:/Users/spcom/Desktop/10DAlerta/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/spcom/Desktop/10DAlerta/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
import { VitePWA } from "file:///C:/Users/spcom/Desktop/10DAlerta/frontend/node_modules/vite-plugin-pwa/dist/index.js";
var vite_config_default = defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "logo10D.png", "SoHoje.png"],
      manifest: {
        name: "10D Alerta - Trading",
        short_name: "10D",
        description: "Advanced Trading Signal System",
        theme_color: "#0a0a0b",
        background_color: "#0a0a0b",
        display: "standalone",
        icons: [
          {
            src: "logo10D.png",
            sizes: "192x192",
            type: "image/png"
          },
          {
            src: "logo10D.png",
            sizes: "512x512",
            type: "image/png"
          }
        ]
      }
    })
  ],
  server: {
    port: 3e3,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxzcGNvbVxcXFxEZXNrdG9wXFxcXDEwREFsZXJ0YVxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcVXNlcnNcXFxcc3Bjb21cXFxcRGVza3RvcFxcXFwxMERBbGVydGFcXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcuanNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L1VzZXJzL3NwY29tL0Rlc2t0b3AvMTBEQWxlcnRhL2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcclxuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0J1xyXG5pbXBvcnQgeyBWaXRlUFdBIH0gZnJvbSAndml0ZS1wbHVnaW4tcHdhJ1xyXG5cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcclxuICAgIHBsdWdpbnM6IFtcclxuICAgICAgICByZWFjdCgpLFxyXG4gICAgICAgIFZpdGVQV0Eoe1xyXG4gICAgICAgICAgICByZWdpc3RlclR5cGU6ICdhdXRvVXBkYXRlJyxcclxuICAgICAgICAgICAgaW5jbHVkZUFzc2V0czogWydmYXZpY29uLnN2ZycsICdsb2dvMTBELnBuZycsICdTb0hvamUucG5nJ10sXHJcbiAgICAgICAgICAgIG1hbmlmZXN0OiB7XHJcbiAgICAgICAgICAgICAgICBuYW1lOiAnMTBEIEFsZXJ0YSAtIFRyYWRpbmcnLFxyXG4gICAgICAgICAgICAgICAgc2hvcnRfbmFtZTogJzEwRCcsXHJcbiAgICAgICAgICAgICAgICBkZXNjcmlwdGlvbjogJ0FkdmFuY2VkIFRyYWRpbmcgU2lnbmFsIFN5c3RlbScsXHJcbiAgICAgICAgICAgICAgICB0aGVtZV9jb2xvcjogJyMwYTBhMGInLFxyXG4gICAgICAgICAgICAgICAgYmFja2dyb3VuZF9jb2xvcjogJyMwYTBhMGInLFxyXG4gICAgICAgICAgICAgICAgZGlzcGxheTogJ3N0YW5kYWxvbmUnLFxyXG4gICAgICAgICAgICAgICAgaWNvbnM6IFtcclxuICAgICAgICAgICAgICAgICAgICB7XHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHNyYzogJ2xvZ28xMEQucG5nJyxcclxuICAgICAgICAgICAgICAgICAgICAgICAgc2l6ZXM6ICcxOTJ4MTkyJyxcclxuICAgICAgICAgICAgICAgICAgICAgICAgdHlwZTogJ2ltYWdlL3BuZydcclxuICAgICAgICAgICAgICAgICAgICB9LFxyXG4gICAgICAgICAgICAgICAgICAgIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgc3JjOiAnbG9nbzEwRC5wbmcnLFxyXG4gICAgICAgICAgICAgICAgICAgICAgICBzaXplczogJzUxMng1MTInLFxyXG4gICAgICAgICAgICAgICAgICAgICAgICB0eXBlOiAnaW1hZ2UvcG5nJ1xyXG4gICAgICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICAgIF1cclxuICAgICAgICAgICAgfVxyXG4gICAgICAgIH0pXHJcbiAgICBdLFxyXG4gICAgc2VydmVyOiB7XHJcbiAgICAgICAgcG9ydDogMzAwMCxcclxuICAgICAgICBob3N0OiB0cnVlLFxyXG4gICAgICAgIHByb3h5OiB7XHJcbiAgICAgICAgICAgICcvYXBpJzoge1xyXG4gICAgICAgICAgICAgICAgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo1MDAxJyxcclxuICAgICAgICAgICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZVxyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfVxyXG4gICAgfVxyXG59KVxyXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQXlULFNBQVMsb0JBQW9CO0FBQ3RWLE9BQU8sV0FBVztBQUNsQixTQUFTLGVBQWU7QUFFeEIsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDeEIsU0FBUztBQUFBLElBQ0wsTUFBTTtBQUFBLElBQ04sUUFBUTtBQUFBLE1BQ0osY0FBYztBQUFBLE1BQ2QsZUFBZSxDQUFDLGVBQWUsZUFBZSxZQUFZO0FBQUEsTUFDMUQsVUFBVTtBQUFBLFFBQ04sTUFBTTtBQUFBLFFBQ04sWUFBWTtBQUFBLFFBQ1osYUFBYTtBQUFBLFFBQ2IsYUFBYTtBQUFBLFFBQ2Isa0JBQWtCO0FBQUEsUUFDbEIsU0FBUztBQUFBLFFBQ1QsT0FBTztBQUFBLFVBQ0g7QUFBQSxZQUNJLEtBQUs7QUFBQSxZQUNMLE9BQU87QUFBQSxZQUNQLE1BQU07QUFBQSxVQUNWO0FBQUEsVUFDQTtBQUFBLFlBQ0ksS0FBSztBQUFBLFlBQ0wsT0FBTztBQUFBLFlBQ1AsTUFBTTtBQUFBLFVBQ1Y7QUFBQSxRQUNKO0FBQUEsTUFDSjtBQUFBLElBQ0osQ0FBQztBQUFBLEVBQ0w7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNKLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNILFFBQVE7QUFBQSxRQUNKLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNsQjtBQUFBLElBQ0o7QUFBQSxFQUNKO0FBQ0osQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
