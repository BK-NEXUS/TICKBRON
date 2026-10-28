// The address of the backend, shared by every adapter. Not set: the local backend. Set to an empty value:
// the same address as the page, so one tunnel (ngrok) to the dev server serves the site and /api and /media.
export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/+$/, '')
