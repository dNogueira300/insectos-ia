import Cabecera from '../../compartido/Cabecera.jsx'
import Pie from '../../compartido/Pie.jsx'

export default function Inicio() {
  return (
    <>
      <Cabecera pagina="inicio" />
      <main id="contenido" className="contenedor">
        <h1>Identifica el orden y la familia de un insecto con una foto</h1>
        <a className="boton boton--principal" href="/identificar/">
          Identificar un insecto
        </a>
      </main>
      <Pie />
    </>
  )
}
