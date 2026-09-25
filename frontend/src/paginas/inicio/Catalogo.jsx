import { useCallback, useEffect, useMemo, useState } from 'react'
import { obtenerResumen } from '../../compartido/api.js'
import PanelFichas from './PanelFichas.jsx'
import TarjetaClase from './TarjetaClase.jsx'

const normalizar = (texto) =>
  (texto ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

export default function Catalogo({ catalogo, error }) {
  const [orden, setOrden] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [abierta, setAbierta] = useState(null)
  // Órdenes con registros en la base, consultados en vivo: la base crece con el
  // Excel de Agronomía y un conteo guardado en catalogo.json quedaría viejo. Si
  // no se puede consultar, todas las tarjetas conservan "Ver fichas".
  const [conFichas, setConFichas] = useState(null)

  useEffect(() => {
    let vigente = true
    obtenerResumen()
      .then(({ por_orden }) => {
        if (vigente) setConFichas(new Set(por_orden.filter((o) => o.registros > 0).map((o) => o.orden)))
      })
      .catch(() => {})
    return () => {
      vigente = false
    }
  }, [])
  const cerrarPanel = useCallback(() => setAbierta(null), [])

  const grupos = useMemo(() => {
    if (!catalogo) return []
    const consulta = normalizar(busqueda.trim())
    return catalogo.ordenes
      .filter((o) => !orden || o.nombre === orden)
      .map((o) => ({
        ...o,
        clases: catalogo.clases.filter(
          (c) =>
            c.orden === o.nombre &&
            (!consulta || normalizar(`${c.nombre} ${c.nombre_comun}`).includes(consulta)),
        ),
      }))
      .filter((grupo) => grupo.clases.length > 0)
  }, [catalogo, orden, busqueda])

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
          <>
            <div className="catalogo__filtros">
              <label className="campo">
                <span>Buscar</span>
                <input
                  type="search"
                  value={busqueda}
                  onChange={(evento) => setBusqueda(evento.target.value)}
                  placeholder="Nombre científico o común"
                />
              </label>
              <div className="catalogo__ordenes" role="group" aria-label="Filtrar por orden">
                <button type="button" className="filtro" aria-pressed={orden === ''} onClick={() => setOrden('')}>
                  Todos
                </button>
                {catalogo.ordenes.map((o) => (
                  <button
                    key={o.nombre}
                    type="button"
                    className="filtro"
                    aria-pressed={orden === o.nombre}
                    onClick={() => setOrden(o.nombre)}
                  >
                    {o.nombre}
                  </button>
                ))}
              </div>
            </div>

            {grupos.length === 0 && (
              <p className="catalogo__vacio">No hay clases que coincidan con la búsqueda.</p>
            )}

            {grupos.map((grupo) => (
              <div
                key={grupo.nombre}
                className="catalogo__grupo"
                // Ancla del orden para el resultado incierto. Los órdenes sin
                // familias ya la tienen en su propia tarjeta.
                id={grupo.clases.some((c) => c.tipo === 'familia') ? `orden-${grupo.nombre}` : undefined}
              >
                <h3 className="catalogo__orden">
                  {grupo.nombre} <span>{grupo.nombre_comun}</span>
                </h3>
                <ul className="catalogo__lista">
                  {grupo.clases.map((clase) => (
                    <li key={clase.id}>
                      <TarjetaClase
                        clase={clase}
                        alAbrir={() => setAbierta(clase)}
                        sinFichas={conFichas !== null && !conFichas.has(clase.orden)}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </>
        )}
      </div>
      {abierta && <PanelFichas clase={abierta} alCerrar={cerrarPanel} />}
    </section>
  )
}
