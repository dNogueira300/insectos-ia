import { CREDITOS } from './creditos.js'

export default function Creditos({ creditos = CREDITOS }) {
  const { grupo, docente, desarrolladores, recolectores } = creditos
  return (
    <section id="creditos" className="creditos" aria-labelledby="titulo-creditos">
      <div className="contenedor">
        <h1 id="titulo-creditos">Créditos</h1>
        <p className="creditos__bajada">Las personas que hicieron posible INSECTIA.</p>
        <dl className="creditos__lista">
          <div className="creditos__grupo">
            <dt>Grupo de investigación</dt>
            <dd>
              <strong>{grupo.nombre}</strong>
              <span>{grupo.detalle}</span>
            </dd>
          </div>
          <div className="creditos__grupo">
            <dt>Docente del curso</dt>
            <dd>
              <strong>{docente.nombre}</strong>
              <span>{docente.detalle}</span>
            </dd>
          </div>
          <div className="creditos__grupo">
            <dt>Desarrollo del sistema</dt>
            {desarrolladores.map((nombre) => (
              <dd key={nombre}>
                <strong>{nombre}</strong>
              </dd>
            ))}
          </div>
          <div className="creditos__grupo creditos__grupo--ancho">
            <dt>Estudiantes recolectores</dt>
            {recolectores.length > 0 ? (
              <dd>
                <ul className="creditos__nombres">
                  {recolectores.map((nombre) => (
                    <li key={nombre}>{nombre}</li>
                  ))}
                </ul>
              </dd>
            ) : (
              <dd className="creditos__pendiente">
                Los nombres de los estudiantes que recolectaron y fotografiaron los ejemplares se
                agregarán pronto.
              </dd>
            )}
          </div>
        </dl>
      </div>
    </section>
  )
}
