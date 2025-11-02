/// <reference types="vite/client" />

// Vite environment variables type declarations
interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  readonly MODE: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly SSR: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// CSS module declarations
declare module '*.css' {
  const content: string
  export default content
}

declare module '*.scss' {
  const content: string
  export default content
}

declare module 'vue-toastification/dist/index.css' {
  const content: string
  export default content
}
