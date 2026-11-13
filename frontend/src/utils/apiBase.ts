// Backend tiń mánzili, hár adapter ortaq paydalanadı. Belgilenbegen: jergilikli backend. Bos mánis penen belgilengen:
// bettiń birdey mánzili, sonda dev serverge bir tunnel (ngrok) saytqa hám /api hám /media ǵa xızmet etedi.
export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/+$/, '')
