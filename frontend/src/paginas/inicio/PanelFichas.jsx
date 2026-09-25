import { useEffect, useRef, useState } from 'react'
import { obtenerTaxon } from '../../compartido/api.js'
import Ficha from '../../compartido/Ficha.jsx'

export default function PanelFichas({ clase, alCerrar }) {
  const [estado, setEstado] = useState({ cargando: true, fichas: [], error: '' })
  const botonCerrar = useRef(null)
  const panel = useRef(null)

  // Con el panel abierto, Tab recorre solo lo que hay dentro: la página de
  // atrás queda inerte, como en un diálogo modal.
  function retenerFoco(evento) {
    const enfocables = panel.current?.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
    )
    if (!enfocables?.length) return
    const primero = enfocables[0]
    const ultimo = enfocables[enfocables.length - 1]
    const dentro = panel.current.contains(document.activeElement)
    if (evento.shiftKey && (document.activeElement === primero || !dentro)) {
      evento.preventDefault()
      ultimo.focus()
    } else if (!evento.shiftKey && (document.activeElement === ultimo || !dentro)) {
      evento.preventDefault()
      primero.focus()
    }
  }

  useEffect(() => {
    let vigente = true
    const familia = clase.tipo === 'familia' ? clase.nombre : ''
    obtenerTaxon(clase.orden, familia)
      .then((datos) => vigente && setEstado({ cargando: false, fichas: datos.fichas, error: '' }))
      .catch((e) => vigente && setEstado({ cargando: false, fichas: [], error: e.message }))
    return () => {
      vigente = false
    }
  }, [clase])

  useEffect(() => {
    // Foco al panel al abrir y de vuelta al botón que lo abrió al cerrar.
    const previo = document.activeElement
    botonCerrar.current?.focus()
    const alTeclear = (evento) => {
      if (evento.key === 'Escape') alCerrar()
      if (evento.key === 'Tab') retenerFoco(evento)
    }
    document.addEventListener('keydown', alTeclear)
    return () => {
      document.removeEventListener('keydown', alTeclear)
      previo?.focus?.()
    }
  }, [alCerrar])

  return (
    <div className="panel__fondo" onClick={alCerrar}>
      <div
        ref={panel}
        className="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-panel"
        onClick={(evento) => evento.stopPropagation()}
      >
        <div className="panel__encabezado">
          <h2 id="titulo-panel" className="cientifico">
            {clase.nombre}
          </h2>
          <button ref={botonCerrar} type="button" className="boton boton--secundario boton--chico" onClick={alCerrar}>
            Cerrar
          </button>
        </div>
        {estado.cargando && <p role="status">Cargando fichas…</p>}
        {estado.error && (
          <p className="aviso aviso--error" role="alert">
            {estado.error}
          </p>
        )}
        {!estado.cargando && !estado.error && (
          <Ficha
            fichas={estado.fichas}
            titulo="Fichas de la base de datos biológica"
            vacio={
              clase.tipo === 'familia'
                ? 'Aún no hay fichas de esta familia en la base.'
                : 'Aún no hay fichas de este orden en la base.'
            }
          />
        )}
      </div>
    </div>
  )
}
