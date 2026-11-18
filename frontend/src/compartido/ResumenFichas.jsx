import { clasificarImportancia } from './importancia.js'
import { resumirRegistros, urlRegistros } from './resumen.js'

const MAX_CULTIVOS = 6
const MAX_TAXONES = 6

// Una sola ficha con el resumen de los registros de la base para un taxón, y el
// enlace a la página con todos los registros. Sin nombres de personas: la base
// trae Colector y Verificado_por, pero la interfaz no los muestra.
export default function ResumenFichas({
  fichas,
  orden,
  familia = '',
  titulo = 'Información de la base de datos',
  vacio = 'No hay registros en la base de datos biológica para este taxón todavía.',
  enlace = true,
}) {
  const r = resumirRegistros(fichas)
  if (r.n === 0) {
    return (
      <section className="ficha">
        <p className="ayuda">{vacio}</p>
      </section>
    )
  }

  const taxon = familia || orden
  const datos = [
    ['Nombres comunes', r.nombres.slice(0, 4).join(', ')],
    ['Tipo de daño', r.danos.slice(0, 3).join(', ')],
    ['Estados registrados', r.estados.join(', ')],
    ['Lugares', r.lugares.slice(0, 3).join(', ')],
  ].filter(([, valor]) => valor)

  return (
    <section className="ficha">
      <h2 className="ficha__titulo">{titulo}</h2>
      <article className="ficha__registro resumen">
        <p className="resumen__origen">
          Resumen de {r.n} {r.n === 1 ? 'registro' : 'registros'} de la base de datos de insectos de la UNAP,
          fotografiados por estudiantes del curso en Loreto. Describen a {familia ? 'la familia' : 'el orden'}{' '}
          <span className={familia ? 'cientifico' : undefined}>{taxon}</span>, no la especie de tu foto.
        </p>

        {r.importancias.length > 0 && (
          <div className="resumen__bloque">
            <h3 className="resumen__rotulo">Importancia registrada</h3>
            <div className="ficha__chips">
              {r.importancias.map(({ texto, n }) => {
                const tipo = clasificarImportancia(texto)
                return (
                  <span key={texto} className={`chip ${tipo ? `chip--${tipo}` : 'chip--neutro'}`}>
                    {texto} · {n}
                  </span>
                )
              })}
            </div>
          </div>
        )}

        {r.cultivos.length > 0 && (
          <div className="resumen__bloque">
            <h3 className="resumen__rotulo">Cultivos donde se registró</h3>
            <div className="ficha__chips">
              {r.cultivos.slice(0, MAX_CULTIVOS).map(({ texto }) => (
                <span key={texto} className="chip chip--cultivo">{texto}</span>
              ))}
            </div>
          </div>
        )}

        <dl className="ficha__datos">
          {datos.map(([etiqueta, valor]) => (
            <div key={etiqueta} className="ficha__dato">
              <dt>{etiqueta}</dt>
              <dd>{valor}</dd>
            </div>
          ))}
          {r.taxones.length > 0 && (
            <div className="ficha__dato">
              <dt>Géneros y especies anotados</dt>
              <dd>
                {r.taxones.slice(0, MAX_TAXONES).map((t, i) => (
                  <span key={t}>
                    {i > 0 && ', '}
                    <span className="cientifico">{t}</span>
                  </span>
                ))}
                {r.taxones.length > MAX_TAXONES && ` y ${r.taxones.length - MAX_TAXONES} más`}
              </dd>
            </div>
          )}
        </dl>

        {enlace && (
          <a className="boton boton--secundario boton--chico resumen__enlace" href={urlRegistros(orden, familia)}>
            {`Ver los ${r.n} ${r.n === 1 ? 'registro' : 'registros'}`}
          </a>
        )}
      </article>
    </section>
  )
}
