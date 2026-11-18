import { useEffect, useState } from 'react'
import Cabecera from '../../compartido/Cabecera.jsx'
import { cargarCatalogo, cargarDemostracion } from '../../compartido/datos.js'
import Pie from '../../compartido/Pie.jsx'
import ComoFunciona from './ComoFunciona.jsx'
import Desempeno from './Desempeno.jsx'
import Portada from './Portada.jsx'
import VistaCatalogo from './VistaCatalogo.jsx'

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

  const nFamilias = catalogo?.clases.filter((c) => c.tipo === 'familia').length

  return (
    <>
      <Cabecera pagina="inicio" />
      <main id="contenido">
        <Portada demostracion={demostracion} nFamilias={nFamilias} />
        <ComoFunciona demostracion={demostracion} />
        {catalogo && <Desempeno metricas={catalogo.metricas} />}
        <VistaCatalogo catalogo={catalogo} error={errorCatalogo} />
      </main>
      <Pie corrida={catalogo?.corrida} />
    </>
  )
}
