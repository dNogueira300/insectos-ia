import Cabecera from '../../compartido/Cabecera.jsx'
import Pie from '../../compartido/Pie.jsx'
import Creditos from './Creditos.jsx'

export default function PaginaCreditos() {
  return (
    <>
      <Cabecera pagina="creditos" />
      <main id="contenido">
        <Creditos />
      </main>
      <Pie />
    </>
  )
}
