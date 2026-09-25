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
        <dl className="desempeno__datos">
          <div>
            <dt>Acierta la familia</dt>
            <dd className="desempeno__cifra">{pct(metricas.exactitud_familia)}</dd>
            <dd className="desempeno__detalle">de las fotos de prueba.</dd>
          </div>
          <div>
            <dt>Cuando se anima a responder</dt>
            <dd className="desempeno__cifra">{pct(metricas.acierta_cuando_responde, 1)}</dd>
            <dd className="desempeno__detalle">
              de acierto. Responde en el {pct(metricas.responde)} de los casos; en el resto dice
              que no está seguro.
            </dd>
          </div>
          <div>
            <dt>Entre sus tres primeras opciones</dt>
            <dd className="desempeno__cifra">{pct(metricas.top3_familia)}</dd>
            <dd className="desempeno__detalle">de las veces está la familia correcta.</dd>
          </div>
        </dl>
      </div>
    </section>
  )
}
