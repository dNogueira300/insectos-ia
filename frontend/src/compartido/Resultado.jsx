import BarraConfianza from './BarraConfianza.jsx'

export default function Resultado({ prediccion, conEnlace = true }) {
  if (!prediccion) return null

  const {
    orden,
    confianza_orden,
    familia,
    confianza_familia,
    familia_incierta,
    top_familias,
  } = prediccion
  // El backend devuelve familia vacía cuando el orden no tiene familias en el
  // sistema: no es una duda del modelo y no se muestra como tal.
  const sinFamilias = !familia && top_familias.length === 0
  const afirmada = !sinFamilias && !familia_incierta

  return (
    <section className="resultado" aria-live="polite">
      <p className="resultado__ruta">
        <span className="resultado__paso">
          <span className="resultado__nivel">Orden</span>
          <strong>{orden}</strong>
        </span>
        {afirmada && (
          <span className="resultado__paso">
            <span className="resultado__flecha" aria-hidden="true">
              →
            </span>
            <span className="resultado__nivel">Familia</span>
            <strong>{familia}</strong>
          </span>
        )}
      </p>

      <BarraConfianza titulo="Seguridad en el orden" valor={confianza_orden} />

      {sinFamilias && (
        <p className="resultado__nota">Este orden no se clasifica por familia en el sistema.</p>
      )}

      {afirmada && (
        <BarraConfianza titulo="Seguridad en la familia" valor={confianza_familia} estado="afirmada" />
      )}

      {!sinFamilias && familia_incierta && (
        <div className="resultado__incierto">
          <BarraConfianza titulo="Seguridad en la familia" valor={confianza_familia} estado="incierta" />
          <p className="resultado__aviso">
            <strong>No se puede determinar la familia con certeza.</strong> Candidatas dentro de{' '}
            {orden}, para revisar con un especialista:
          </p>
          <ul className="resultado__candidatas">
            {top_familias.map(({ familia: nombre, confianza }) => (
              <li key={nombre}>
                <BarraConfianza titulo={nombre} valor={confianza} estado="candidata" />
              </li>
            ))}
          </ul>
        </div>
      )}

      {conEnlace && (
        <a className="resultado__enlace" href={afirmada ? `/#familia-${familia}` : `/#orden-${orden}`}>
          {afirmada ? 'Ver esta familia en el catálogo' : 'Ver este orden en el catálogo'}
        </a>
      )}
    </section>
  )
}
