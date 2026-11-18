import { useEffect, useState } from 'react'
import Cabecera from '../../compartido/Cabecera.jsx'
import { cargarCatalogo } from '../../compartido/datos.js'
import Pie from '../../compartido/Pie.jsx'
import Catalogo from './Catalogo.jsx'

export default function PaginaCatalogo() {
  const [catalogo, setCatalogo] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    cargarCatalogo()
      .then(setCatalogo)
      .catch((e) => setError(e.message))
  }, [])

  // Un enlace como /catalogo/#familia-Apidae (desde la herramienta) llega a su
  // tarjeta cuando el catálogo ya se dibujó.
  useEffect(() => {
    if (!catalogo || !window.location.hash) return
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView?.({ block: 'center' })
  }, [catalogo])

  return (
    <>
      <Cabecera pagina="catalogo" />
      <main id="contenido">
        <Catalogo catalogo={catalogo} error={error} />
      </main>
      <Pie corrida={catalogo?.corrida} />
    </>
  )
}
