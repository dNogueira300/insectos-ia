import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import './creditos.css'
import PaginaCreditos from './PaginaCreditos.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PaginaCreditos />
  </StrictMode>,
)
