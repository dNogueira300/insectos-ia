import { textoLicencia } from '../../compartido/Credito.jsx'

// Se rotula la respuesta real para que un resultado incierto o distinto se lea
// como lo que es: una demostración, no un error escondido.
function rotulo({ real }) {
  return real.familia ? `Familia real: ${real.familia}` : `Orden real: ${real.orden}`
}

export default function Ejemplos({ ejemplos, alElegir, ocupado }) {
  if (!ejemplos?.length) return null
  return (
    <section className="ejemplos" aria-labelledby="titulo-ejemplos">
      <h2 id="titulo-ejemplos" className="ejemplos__titulo">
        Probar con un ejemplo
      </h2>
      <ul className="ejemplos__lista">
        {ejemplos.map((ejemplo) => (
          <li key={ejemplo.archivo}>
            <button
              type="button"
              className="ejemplos__boton"
              disabled={ocupado}
              onClick={() => alElegir(ejemplo)}
            >
              <img src={ejemplo.archivo} alt="" loading="lazy" />
              <span className="ejemplos__rotulo">{rotulo(ejemplo)}</span>
            </button>
          </li>
        ))}
      </ul>
      <p className="ejemplos__nota">
        Fotos que el modelo no vio al entrenar. Créditos:{' '}
        {ejemplos.map((e) => `${e.credito} (${textoLicencia(e.licencia)})`).join('; ')}.
      </p>
    </section>
  )
}
