import { useEffect, useState } from 'react'

// Los formatos que el backend sabe abrir. HEIC queda fuera a propósito.
const TIPOS = 'image/jpeg,image/png,image/webp'

function esTactil() {
  return window.matchMedia?.('(pointer: coarse)')?.matches === true
}

export default function ZonaFoto({ alSeleccionar, ocupado, vistaPrevia }) {
  // Cambiar la clave monta selectores nuevos y vacíos: sin esto, elegir otra
  // vez la misma foto (por ejemplo, para reintentar) no avisa nada.
  const [clave, setClave] = useState(0)
  const [arrastrando, setArrastrando] = useState(false)
  const [tactil, setTactil] = useState(false)

  useEffect(() => setTactil(esTactil()), [])

  function entregar(archivo) {
    if (!archivo || ocupado) return
    setClave((valor) => valor + 1)
    alSeleccionar(archivo)
  }

  return (
    <div
      className={`zona${arrastrando ? ' zona--arrastrando' : ''}`}
      onDragOver={(evento) => {
        evento.preventDefault()
        setArrastrando(true)
      }}
      onDragLeave={() => setArrastrando(false)}
      onDrop={(evento) => {
        evento.preventDefault()
        setArrastrando(false)
        entregar(evento.dataTransfer?.files?.[0])
      }}
    >
      <div className="zona__marco marco">
        {vistaPrevia ? (
          <img className="zona__foto" src={vistaPrevia} alt="Foto elegida" />
        ) : (
          <p className="zona__vacio">
            {tactil
              ? 'Toma una foto o elígela de tu galería.'
              : 'Arrastra una foto aquí o elígela desde tu equipo.'}
          </p>
        )}
        {ocupado && (
          <div className="zona__ocupado" role="status">
            <span className="zona__indicador" aria-hidden="true" />
            Identificando…
          </div>
        )}
      </div>

      {/* En el celular, en campo, lo natural es tomar la foto: va primero. */}
      <div className="zona__acciones" key={clave}>
        {tactil && (
          <label className="boton boton--principal">
            Tomar foto
            <input
              className="visualmente-oculto"
              type="file"
              accept="image/*"
              capture="environment"
              disabled={ocupado}
              onChange={(evento) => entregar(evento.target.files?.[0])}
            />
          </label>
        )}
        <label className={`boton ${tactil ? 'boton--secundario' : 'boton--principal'}`}>
          Elegir foto
          <input
            className="visualmente-oculto"
            type="file"
            accept={TIPOS}
            disabled={ocupado}
            onChange={(evento) => entregar(evento.target.files?.[0])}
          />
        </label>
      </div>
    </div>
  )
}
