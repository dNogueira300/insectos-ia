import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import './catalogo.css'
import PaginaCatalogo from './PaginaCatalogo.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PaginaCatalogo />
  </StrictMode>,
)
