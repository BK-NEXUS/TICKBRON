/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_PAYMENT_TEST_MODE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
