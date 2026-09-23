const porcentaje = (valor) => `${Math.round(valor * 100)} %`

export default function Resultado({ prediccion }) {
  if (!prediccion) return null

  const { orden, confianza_orden, familia, confianza_familia, familia_incierta, top_familias } =
    prediccion

  return (
    <section className="resultado">
      <div className="nivel">
        <span className="etiqueta">Orden</span>
        <strong className="valor">{orden}</strong>
        <span className="confianza">{porcentaje(confianza_orden)}</span>
      </div>

      {!familia && top_familias.length === 0 ? (
        // El backend devuelve familia vacía cuando el orden no tiene familias
        // en el sistema: no es una duda del modelo, así que no se muestra como tal.
        <div className="nivel">
          <span className="etiqueta">Familia</span>
          <p className="ayuda">Este orden no se clasifica por familia en el sistema.</p>
        </div>
      ) : familia_incierta ? (
        <div className="nivel incierto">
          <span className="etiqueta">Familia</span>
          <strong className="valor">No se puede determinar con certeza</strong>
          {top_familias.length > 0 && (
            <>
              <p className="ayuda">
                Candidatas dentro de {orden}, para revisar con un especialista:
              </p>
              <ul className="candidatas">
                {top_familias.map(({ familia: nombre, confianza }) => (
                  <li key={nombre}>
                    <span>{nombre}</span>
                    <span className="confianza">{porcentaje(confianza)}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      ) : (
        <div className="nivel">
          <span className="etiqueta">Familia</span>
          <strong className="valor">{familia}</strong>
          <span className="confianza">{porcentaje(confianza_familia)}</span>
        </div>
      )}
    </section>
  )
}
