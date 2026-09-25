export default function Cabecera({ pagina }) {
  return (
    <header className="cabecera">
      <div className="contenedor cabecera__fila">
        <a className="cabecera__marca" href="/" aria-label="INSECTIA, inicio">
          <img className="cabecera__logo" src="/marca/logo-horizontal.webp" alt="" />
          <img className="cabecera__simbolo" src="/marca/simbolo.webp" alt="" />
        </a>
        <nav className="cabecera__nav" aria-label="Principal">
          <a
            className="cabecera__enlace"
            href="/"
            aria-current={pagina === 'inicio' ? 'page' : undefined}
          >
            Inicio
          </a>
          <a className="cabecera__enlace" href="/#catalogo">
            Catálogo
          </a>
          <a
            className="boton boton--principal"
            href="/identificar/"
            aria-current={pagina === 'identificar' ? 'page' : undefined}
          >
            Identificar un insecto
          </a>
        </nav>
      </div>
    </header>
  )
}
