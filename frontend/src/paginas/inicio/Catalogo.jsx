import { useCallback, useMemo, useState } from 'react'
import PanelFichas from './PanelFichas.jsx'
import TarjetaClase from './TarjetaClase.jsx'

const normalizar = (texto) =>
  (texto ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

export default function Catalogo({ catalogo, error }) {
  const [orden, setOrden] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [abierta, setAbierta] = useState(null)
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
              <div key={grupo.nombre} className="catalogo__grupo">
                <h3 className="catalogo__orden">
                  {grupo.nombre} <span>{grupo.nombre_comun}</span>
                </h3>
                <ul className="catalogo__lista">
                  {grupo.clases.map((clase) => (
                    <li key={clase.id}>
                      <TarjetaClase clase={clase} alAbrir={() => setAbierta(clase)} />
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
