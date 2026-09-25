import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import Inicio from './Inicio.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Inicio />
  </StrictMode>,
)
