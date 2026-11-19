import { useEffect, useRef, useState } from 'react'

// En el celular (hasta 640 px, ver .cabecera en base.css) los enlaces van en un
// menú que se abre con el botón ☰; en la computadora se ven siempre y el botón
// del menú no aparece. «Identificar un insecto» queda siempre a la vista.
export default function Cabecera({ pagina }) {
  const [abierto, setAbierto] = useState(false)
  const cabecera = useRef(null)
  const botonMenu = useRef(null)

  useEffect(() => {
    if (!abierto) return undefined
    function alPulsarTecla(evento) {
      if (evento.key === 'Escape') {
        setAbierto(false)
        botonMenu.current?.focus()
      }
    }
    function alPulsarFuera(evento) {
      if (!cabecera.current?.contains(evento.target)) setAbierto(false)
    }
    document.addEventListener('keydown', alPulsarTecla)
    document.addEventListener('pointerdown', alPulsarFuera)
    return () => {
      document.removeEventListener('keydown', alPulsarTecla)
      document.removeEventListener('pointerdown', alPulsarFuera)
    }
  }, [abierto])

  return (
    <header ref={cabecera} className={abierto ? 'cabecera cabecera--abierta' : 'cabecera'}>
      <div className="contenedor cabecera__fila">
        <a className="cabecera__marca" href="/" aria-label="INSECTIA, inicio">
          <img className="cabecera__logo" src="/marca/logo-horizontal.webp" alt="" />
          <img className="cabecera__simbolo" src="/marca/simbolo.webp" alt="" />
        </a>
        <a
          className="boton boton--principal cabecera__boton"
          href="/identificar/"
          aria-current={pagina === 'identificar' ? 'page' : undefined}
          aria-label="Identificar un insecto"
        >
          {/* .boton es inline-flex: el espacio entre las dos partes lo pone su gap. */}
          Identificar<span className="cabecera__boton-resto">un insecto</span>
        </a>
        <button
          ref={botonMenu}
          type="button"
          className="cabecera__menu"
          aria-expanded={abierto}
          aria-controls="menu-principal"
          aria-label={abierto ? 'Cerrar el menú' : 'Abrir el menú'}
          onClick={() => setAbierto((valor) => !valor)}
        >
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false">
            {abierto ? (
              <path d="M6 6l12 12M18 6L6 18" />
            ) : (
              <path d="M4 7h16M4 12h16M4 17h16" />
            )}
          </svg>
        </button>
        <nav id="menu-principal" className="cabecera__nav" aria-label="Principal">
          <a
            className="cabecera__enlace"
            href="/"
            aria-current={pagina === 'inicio' ? 'page' : undefined}
          >
            Inicio
          </a>
          <a
            className="cabecera__enlace"
            href="/catalogo/"
            aria-current={pagina === 'catalogo' ? 'page' : undefined}
          >
            Catálogo
          </a>
          <a
            className="cabecera__enlace"
            href="/creditos/"
            aria-current={pagina === 'creditos' ? 'page' : undefined}
          >
            Créditos
          </a>
        </nav>
      </div>
    </header>
  )
}
