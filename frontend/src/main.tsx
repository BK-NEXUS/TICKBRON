import './styles/tokens.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
// Brand fonts, bundled with the app (the CSP only allows same-origin styles and fonts)
import '@fontsource/pt-sans/400.css'
import '@fontsource/pt-sans/700.css'
import '@fontsource/pt-serif/400.css'
import '@fontsource/pt-serif/700.css'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
