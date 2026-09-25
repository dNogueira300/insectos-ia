export default function Pie({ corrida }) {
  return (
    <footer className="pie">
      <div className="contenedor pie__fila">
        <div>
          <img className="pie__simbolo" src="/marca/simbolo-claro.webp" alt="" />
          <p className="pie__marca">INSECTIA</p>
          <p>
            Universidad Nacional de la Amazonía Peruana · Facultad de Agronomía · Proyecto
            Formativo INAAM–FISI
          </p>
        </div>
        <ul className="pie__datos">
          <li>Fotos: iNaturalist, con el crédito de cada autor.</li>
          {corrida && <li>Modelo: {corrida}</li>}
          <li>
            <a href="/identificar/">Identificar un insecto</a>
          </li>
        </ul>
      </div>
    </footer>
  )
}
