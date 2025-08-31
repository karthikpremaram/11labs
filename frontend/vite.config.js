import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Use the classic JSX runtime so files must import React explicitly.
// This prevents editors/organizers from removing the React import
// (the automatic runtime can make the import appear unused).
export default defineConfig({
  plugins: [react({ jsxRuntime: 'classic' })],
  server: {
    port: 5173,
    strictPort: true,
  },
})
