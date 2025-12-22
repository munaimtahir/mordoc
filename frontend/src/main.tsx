import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './ui/App'

// Import Google Fonts
const fontsLink = document.createElement('link')
fontsLink.href = 'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+3:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap'
fontsLink.rel = 'stylesheet'
document.head.appendChild(fontsLink)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
