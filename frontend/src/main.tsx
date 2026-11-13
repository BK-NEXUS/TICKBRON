import './styles/tokens.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
// Ilova menen birge qaptalǵan brend shriftleri (CSP tek bir kelip shıǵıwdaǵı stil hám shriftlerge ruxsat beredi)
import '@fontsource/pt-sans/400.css'
import '@fontsource/pt-sans/700.css'
import '@fontsource/pt-serif/400.css'
import '@fontsource/pt-serif/700.css'
import './styles/index.css'
import './styles/surfaces.css'
import './styles/refresh.css'
import './styles/panels.css'
import './styles/chat.css'
import { registerServiceWorker } from './pwa/registerServiceWorker'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

window.addEventListener('load', () => void registerServiceWorker())
