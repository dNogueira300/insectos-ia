import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import Identificar from './Identificar.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Identificar />
  </StrictMode>,
)
