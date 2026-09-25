const pct = (valor, decimales = 0) => `${(valor * 100).toFixed(decimales)} %`

export default function Desempeno({ metricas }) {
  return (
    <section className="desempeno" aria-labelledby="titulo-desempeno">
      <div className="contenedor desempeno__rejilla">
        <div>
          <h2 id="titulo-desempeno">Qué tan bien funciona</h2>
          <p>
            Lo medimos con {metricas.n_prueba} fotos que el modelo nunca vio al entrenar, de
            fotógrafos que tampoco vio.
          </p>
          <p className="desempeno__aviso">
            Medido con fotos de catálogo. La evaluación con fotos de campo está pendiente.
          </p>
        </div>
        {/* Frases con la cifra dentro: sin la plantilla de cifra grande con rótulo. */}
        <ul className="desempeno__datos">
          <li>
            Acierta la familia en el <strong>{pct(metricas.exactitud_familia)}</strong> de las fotos
            de prueba.
          </li>
          <li>
            Cuando se anima a responder, acierta el{' '}
            <strong>{pct(metricas.acierta_cuando_responde, 1)}</strong>: responde en el{' '}
            {pct(metricas.responde)} de los casos, y en el resto dice que no está seguro.
          </li>
          <li>
            La familia correcta está entre sus tres primeras opciones el{' '}
            <strong>{pct(metricas.top3_familia)}</strong> de las veces.
          </li>
        </ul>
      </div>
    </section>
  )
}
