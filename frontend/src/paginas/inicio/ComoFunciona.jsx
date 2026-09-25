import Credito from '../../compartido/Credito.jsx'
import Resultado from '../../compartido/Resultado.jsx'

const POSICIONES = ['primera', 'segunda', 'tercera']

// Qué habría pasado si el sistema afirmaba su primera candidata. Se calcula con
// la respuesta real de la foto de prueba; nunca se escribe a mano.
function leccion({ real, prediccion }) {
  const candidatas = prediccion.top_familias.map((t) => t.familia)
  const posicion = candidatas.indexOf(real.familia)
  if (!real.familia || posicion < 0) return null
  if (posicion === 0) {
    return `La familia correcta era ${real.familia}, su primera candidata, pero con menos del 70 % de seguridad no la afirmó.`
  }
  return `La familia correcta era ${real.familia}, su ${POSICIONES[posicion]} candidata: afirmar ${candidatas[0]} habría sido un error.`
}

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
            {leccion(incierto) && <p className="como__leccion">{leccion(incierto)}</p>}
            <Credito foto={incierto} />
          </figcaption>
        </figure>
      )}
    </section>
  )
}
