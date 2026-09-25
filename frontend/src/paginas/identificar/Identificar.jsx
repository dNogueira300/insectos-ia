import Cabecera from '../../compartido/Cabecera.jsx'
import Pie from '../../compartido/Pie.jsx'

export default function Identificar() {
  return (
    <>
      <Cabecera pagina="identificar" />
      <main id="contenido" className="contenedor">
        <h1>Identificar un insecto</h1>
      </main>
      <Pie />
    </>
  )
}
