import Credito from '../../compartido/Credito.jsx'
import Resultado from '../../compartido/Resultado.jsx'

export default function Portada({ demostracion, nFamilias }) {
  const principal = demostracion?.principal
  return (
    <section className="portada">
      <div className="contenedor portada__rejilla">
        <div className="portada__texto">
          <h1>Identifica el orden y la familia de un insecto con una foto</h1>
          <p className="portada__bajada">
            Sistema de Inteligencia Artificial para la identificación de órdenes y familias de
            insectos de importancia económica de la Amazonía peruana.
          </p>
          <div className="portada__acciones">
            <a className="boton boton--claro" href="/identificar/">
              Identificar un insecto
            </a>
            <a className="boton boton--contorno" href="#catalogo">
              {nFamilias ? `Ver las ${nFamilias} familias` : 'Ver las familias'}
            </a>
          </div>
        </div>

        {principal && (
          <figure className="portada__demo">
            <div className="marco marco--claro">
              <img
                src={principal.archivo}
                alt={`Foto de ejemplo: ${principal.real.familia || principal.real.orden}`}
              />
            </div>
            <figcaption className="portada__leyenda">
              <p className="portada__rotulo">Resultado real del modelo con esta foto</p>
              <Resultado prediccion={principal.prediccion} conEnlace={false} />
              <Credito foto={principal} />
            </figcaption>
          </figure>
        )}
      </div>
    </section>
  )
}
