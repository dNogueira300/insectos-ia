import { useEffect, useState } from 'react'
import Cabecera from '../../compartido/Cabecera.jsx'
import { cargarCatalogo, cargarDemostracion } from '../../compartido/datos.js'
import Pie from '../../compartido/Pie.jsx'
import Catalogo from './Catalogo.jsx'
import ComoFunciona from './ComoFunciona.jsx'
import Desempeno from './Desempeno.jsx'
import Portada from './Portada.jsx'

export default function Inicio() {
  const [catalogo, setCatalogo] = useState(null)
  const [errorCatalogo, setErrorCatalogo] = useState('')
  const [demostracion, setDemostracion] = useState(null)

  useEffect(() => {
    cargarCatalogo()
      .then(setCatalogo)
      .catch((e) => setErrorCatalogo(e.message))
    cargarDemostracion()
      .then(setDemostracion)
      .catch(() => setDemostracion(null))
  }, [])

  // Un enlace como /#familia-Apidae (desde la herramienta) llega a su tarjeta
  // cuando el catálogo ya se dibujó.
  useEffect(() => {
    if (!catalogo || !window.location.hash) return
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView?.({ block: 'center' })
  }, [catalogo])

  const nFamilias = catalogo?.clases.filter((c) => c.tipo === 'familia').length

  return (
    <>
      <Cabecera pagina="inicio" />
      <main id="contenido">
        <Portada demostracion={demostracion} nFamilias={nFamilias} />
        <ComoFunciona demostracion={demostracion} />
        {catalogo && <Desempeno metricas={catalogo.metricas} />}
        <Catalogo catalogo={catalogo} error={errorCatalogo} />
      </main>
      <Pie corrida={catalogo?.corrida} />
    </>
  )
}
