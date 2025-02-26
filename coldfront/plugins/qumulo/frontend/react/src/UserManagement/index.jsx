import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './UserManagment.jsx'

createRoot(document.getElementById('user_management')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
