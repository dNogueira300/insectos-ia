import { useEffect, useState } from 'react'
import { obtenerSalud, predecir } from './api.js'
import Resultado from './componentes/Resultado.jsx'
import SubirFoto from './componentes/SubirFoto.jsx'
import './estilos.css'

export default function App() {
  const [prediccion, setPrediccion] = useState(null)
  const [error, setError] = useState(null)
  const [ocupado, setOcupado] = useState(false)
  const [salud, setSalud] = useState(null)

  useEffect(() => {
    obtenerSalud().then(setSalud).catch((e) => setError(e.message))
  }, [])

  async function identificar(archivo) {
    setOcupado(true)
    setError(null)
    setPrediccion(null)
    try {
      setPrediccion(await predecir(archivo))
    } catch (e) {
      setError(e.message)
    } finally {
      setOcupado(false)
    }
  }

  return (
    <main className="app">
      <header>
        <h1>Identificador de insectos amazónicos</h1>
        <p className="subtitulo">Sube una foto y el sistema propone el orden y la familia.</p>
      </header>

      <SubirFoto alSeleccionar={identificar} ocupado={ocupado} />

      {error && <p className="error">{error}</p>}

      <Resultado prediccion={prediccion} />

      {salud && (
        <footer className="pie">
          Modelo con {salud.n_ordenes} órdenes y {salud.n_familias} familias
          {!salud.bd_disponible && ' · base de datos biológica aún no cargada'}
        </footer>
      )}
    </main>
  )
}
