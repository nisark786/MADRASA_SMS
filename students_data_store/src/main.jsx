import { initializeTracing } from './tracing'; // Lazy load tracing
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Initialize tracing asynchronously (non-blocking)
initializeTracing().catch(console.error);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
