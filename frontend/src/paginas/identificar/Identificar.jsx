import { useEffect, useRef, useState } from 'react'
import { predecir } from '../../compartido/api.js'
import Cabecera from '../../compartido/Cabecera.jsx'
import { archivoDesdeRuta, cargarDemostracion } from '../../compartido/datos.js'
import Ficha from '../../compartido/Ficha.jsx'
import Pie from '../../compartido/Pie.jsx'
import Resultado from '../../compartido/Resultado.jsx'
import Consejos from './Consejos.jsx'
import Ejemplos from './Ejemplos.jsx'
import ZonaFoto from './ZonaFoto.jsx'

export default function Identificar() {
  const [estado, setEstado] = useState('vacio') // vacio | identificando | resultado | error
  const [prediccion, setPrediccion] = useState(null)
  const [error, setError] = useState('')
  const [vistaPrevia, setVistaPrevia] = useState(null)
  const [ejemplos, setEjemplos] = useState([])
  // Cómo volver a obtener el archivo del último intento, para "Reintentar".
  const ultimoIntento = useRef(null)
  // URL creada con createObjectURL: se libera al reemplazarla o al salir.
  const urlPropia = useRef(null)
  // En el celular el resultado queda debajo de la foto, los consejos y los
  // ejemplos: sin esto, quien toca "Elegir foto" no ve la respuesta.
  const columnaResultado = useRef(null)

  useEffect(() => {
    cargarDemostracion()
      .then((demostracion) => setEjemplos(demostracion.ejemplos))
      .catch(() => setEjemplos([]))
    return () => urlPropia.current && URL.revokeObjectURL(urlPropia.current)
  }, [])

  useEffect(() => {
    if (estado !== 'resultado' && estado !== 'error') return
    const columna = columnaResultado.current
    const arriba = columna.getBoundingClientRect().top
    if (arriba >= 0 && arriba < window.innerHeight * 0.6) return
    const reducir = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    columna.scrollIntoView({ block: 'start', behavior: reducir ? 'auto' : 'smooth' })
  }, [estado])

  function mostrarFoto(url, esPropia) {
    if (urlPropia.current) URL.revokeObjectURL(urlPropia.current)
    urlPropia.current = esPropia ? url : null
    setVistaPrevia(url)
  }

  async function identificar(obtenerArchivo) {
    ultimoIntento.current = obtenerArchivo
    setEstado('identificando')
    setError('')
    setPrediccion(null)
    try {
      const archivo = await obtenerArchivo()
      setPrediccion(await predecir(archivo))
      setEstado('resultado')
    } catch (e) {
      setError(e.message)
      setEstado('error')
    }
  }

  function alElegirArchivo(archivo) {
    mostrarFoto(URL.createObjectURL(archivo), true)
    identificar(async () => archivo)
  }

  function alElegirEjemplo(ejemplo) {
    mostrarFoto(ejemplo.archivo, false)
    const nombre = ejemplo.archivo.split('/').pop()
    identificar(() => archivoDesdeRuta(ejemplo.archivo, nombre))
  }

  function reiniciar() {
    mostrarFoto(null, false)
    setPrediccion(null)
    setError('')
    setEstado('vacio')
  }

  const ocupado = estado === 'identificando'
  const deOrden = prediccion && (prediccion.familia_incierta || !prediccion.familia)

  return (
    <>
      <Cabecera pagina="identificar" />
      <main id="contenido" className="contenedor identificar">
        <div className="identificar__intro">
          <h1>Identificar un insecto</h1>
          <p>Sube una foto: el sistema propone el orden y, si está seguro, la familia.</p>
        </div>

        <div className="identificar__columnas">
          <div className="identificar__foto">
            <ZonaFoto alSeleccionar={alElegirArchivo} ocupado={ocupado} vistaPrevia={vistaPrevia} />
            <Consejos abierto={estado === 'vacio'} />
            <Ejemplos ejemplos={ejemplos} alElegir={alElegirEjemplo} ocupado={ocupado} />
          </div>

          <div className="identificar__resultado" ref={columnaResultado}>
            {estado === 'vacio' && (
              <p className="identificar__espera">
                Aquí aparecerán el orden, la familia y la ficha biológica de la base.
              </p>
            )}
            {estado === 'error' && (
              <div className="aviso aviso--error" role="alert">
                <p>{error}</p>
                <button
                  type="button"
                  className="boton boton--secundario"
                  onClick={() => identificar(ultimoIntento.current)}
                >
                  Reintentar
                </button>
              </div>
            )}
            {estado === 'resultado' && (
              <>
                <Resultado prediccion={prediccion} />
                <Ficha
                  fichas={prediccion.fichas}
                  titulo={
                    deOrden ? `Registros del orden ${prediccion.orden} en la base` : 'Información biológica'
                  }
                  vacio="Aún no hay fichas de este insecto en la base de datos biológica."
                />
                <button type="button" className="boton boton--secundario" onClick={reiniciar}>
                  Identificar otra foto
                </button>
              </>
            )}
          </div>
        </div>
      </main>
      <Pie />
    </>
  )
}
