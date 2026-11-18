import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import './registros.css'
import PaginaRegistros from './PaginaRegistros.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PaginaRegistros />
  </StrictMode>,
)
