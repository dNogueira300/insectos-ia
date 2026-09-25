import Resultado from '../../compartido/Resultado.jsx'

export default function ComoFunciona({ demostracion }) {
  const incierto = demostracion?.incierto
  return (
    <section className="contenedor como" aria-labelledby="titulo-como">
      <h2 id="titulo-como">Cómo funciona</h2>
      <ol className="como__pasos">
        <li>
          <h3>Subes una foto</h3>
          <p>Desde el celular o la computadora, con el insecto bien visible.</p>
        </li>
        <li>
          <h3>El modelo decide el orden</h3>
          <p>Por ejemplo, si es un escarabajo (Coleoptera) o una mariposa (Lepidoptera).</p>
        </li>
        <li>
          <h3>Y la familia dentro de ese orden</h3>
          <p>
            Solo la afirma si está seguro en al menos un 70 %. Si no, muestra las tres familias
            más probables para que las revise un especialista.
          </p>
        </li>
      </ol>

      {incierto && (
        <figure className="como__ejemplo">
          <div className="marco">
            <img src={incierto.archivo} alt={`Foto de ejemplo: ${incierto.real.orden}`} loading="lazy" />
          </div>
          <figcaption className="como__leyenda">
            <p className="como__rotulo">Un caso real en que el sistema prefiere no afirmar la familia</p>
            <Resultado prediccion={incierto.prediccion} conEnlace={false} />
            <p className="credito">
              Foto: {incierto.credito} · {incierto.licencia.toUpperCase()}
            </p>
          </figcaption>
        </figure>
      )}
    </section>
  )
}
