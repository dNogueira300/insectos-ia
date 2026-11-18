import { useEffect, useState } from 'react'
import { obtenerTaxon } from '../../compartido/api.js'
import Cabecera from '../../compartido/Cabecera.jsx'
import Ficha from '../../compartido/Ficha.jsx'
import Pie from '../../compartido/Pie.jsx'
import ResumenFichas from '../../compartido/ResumenFichas.jsx'

// Todos los registros de la base para una familia (u orden), con la explicación
// de dónde salen. Se llega desde el resultado o desde el catálogo:
// /registros/?orden=Coleoptera&familia=Curculionidae
export default function PaginaRegistros() {
  const parametros = new URLSearchParams(window.location.search)
  const orden = parametros.get('orden') ?? ''
  const familia = parametros.get('familia') ?? ''
  const taxon = familia || orden
  const [estado, setEstado] = useState({ cargando: Boolean(orden), fichas: [], error: '' })

  useEffect(() => {
    if (!orden) return undefined
    let vigente = true
    obtenerTaxon(orden, familia)
      .then((datos) => vigente && setEstado({ cargando: false, fichas: datos.fichas, error: '' }))
      .catch((e) => vigente && setEstado({ cargando: false, fichas: [], error: e.message }))
    return () => {
      vigente = false
    }
  }, [orden, familia])

  return (
    <>
      <Cabecera pagina="catalogo" />
      <main id="contenido" className="registros">
        <div className="contenedor registros__cuerpo">
          <a className="registros__volver" href={familia ? `/catalogo/#familia-${familia}` : '/catalogo/'}>
            ← Volver al catálogo
          </a>
          {!orden ? (
            <>
              <h1>Registros de la base</h1>
              <p>
                Elige una familia en el catálogo para ver sus registros.{' '}
                <a href="/catalogo/">Ir al catálogo</a>
              </p>
            </>
          ) : (
            <>
              <h1>
                Registros de <span className={familia ? 'cientifico' : undefined}>{taxon}</span>
              </h1>
              <div className="registros__origen">
                <p>
                  Estos registros forman parte de la <strong>base de datos de insectos del proyecto INSECTIA</strong>{' '}
                  (UNAP). Cada uno corresponde a una fotografía tomada en 2026 por estudiantes del curso
                  Entomología General y Aplicada, en cultivos y bosques de Loreto, y revisada por el equipo del
                  proyecto.
                </p>
                <p>
                  Muestran qué insectos de este grupo se encontraron en la zona y en qué cultivos: no son la
                  identificación de tu foto.
                </p>
              </div>
              {estado.cargando && <p role="status">Cargando registros…</p>}
              {estado.error && (
                <p className="aviso aviso--error" role="alert">
                  {estado.error}
                </p>
              )}
              {!estado.cargando && !estado.error && (
                <>
                  <ResumenFichas
                    fichas={estado.fichas}
                    orden={orden}
                    familia={familia}
                    titulo="Resumen"
                    enlace={false}
                    vacio="Aún no hay registros de este grupo en la base."
                  />
                  {estado.fichas.length > 0 && (
                    <Ficha fichas={estado.fichas} titulo="Todos los registros" visibles={12} />
                  )}
                </>
              )}
            </>
          )}
        </div>
      </main>
      <Pie />
    </>
  )
}
