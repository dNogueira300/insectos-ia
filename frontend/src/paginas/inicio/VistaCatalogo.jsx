import { useCallback, useMemo, useState } from 'react'
import { useOrdenesConFichas } from '../catalogo/conFichas.js'
import PanelFichas from '../catalogo/PanelFichas.jsx'
import TarjetaClase from '../catalogo/TarjetaClase.jsx'
import { elegirMuestra } from './muestra.js'

export default function VistaCatalogo({ catalogo, error }) {
  const [abierta, setAbierta] = useState(null)
  const conFichas = useOrdenesConFichas()
  const cerrarPanel = useCallback(() => setAbierta(null), [])
  const muestra = useMemo(() => (catalogo ? elegirMuestra(catalogo.clases) : []), [catalogo])

  return (
    <section id="catalogo" className="catalogo" aria-labelledby="titulo-catalogo">
      <div className="contenedor">
        <h2 id="titulo-catalogo">Catálogo de familias</h2>
        <p className="catalogo__bajada">
          Las familias y órdenes que el sistema reconoce, con una foto de ejemplo y qué tan bien
          las distingue el modelo.
        </p>

        {error && (
          <p className="aviso aviso--error" role="alert">
            {error}
          </p>
        )}
        {!catalogo && !error && <p role="status">Cargando el catálogo…</p>}

        {catalogo && (
          <ul className="catalogo__lista vista-catalogo__lista">
            {muestra.map((clase) => (
              <li key={clase.id}>
                <TarjetaClase
                  clase={clase}
                  alAbrir={() => setAbierta(clase)}
                  sinFichas={conFichas !== null && !conFichas.has(clase.orden)}
                />
              </li>
            ))}
          </ul>
        )}

        <a className="boton boton--principal vista-catalogo__enlace" href="/catalogo/">
          Ver catálogo completo
        </a>
      </div>
      {abierta && <PanelFichas clase={abierta} alCerrar={cerrarPanel} />}
    </section>
  )
}
