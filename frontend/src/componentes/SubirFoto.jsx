import { useEffect, useState } from 'react'

export default function SubirFoto({ alSeleccionar, ocupado }) {
  const [vistaPrevia, setVistaPrevia] = useState(null)
  // Cambiar la clave monta un selector nuevo y vacío. Sin esto, elegir otra vez
  // la misma foto (por ejemplo, para reintentar tras un error) no avisa nada.
  const [clave, setClave] = useState(0)

  // Libera la URL de la vista previa anterior al reemplazarla o al desmontar.
  useEffect(() => () => vistaPrevia && URL.revokeObjectURL(vistaPrevia), [vistaPrevia])

  function manejar(evento) {
    const archivo = evento.target.files?.[0]
    if (!archivo) return
    setVistaPrevia(URL.createObjectURL(archivo))
    setClave((valor) => valor + 1)
    alSeleccionar(archivo)
  }

  return (
    <div className="subir">
      <label className="boton">
        {ocupado ? 'Identificando…' : 'Elegir foto del insecto'}
        <input
          key={clave}
          type="file"
          accept="image/*"
          onChange={manejar}
          disabled={ocupado}
          hidden
        />
      </label>
      {vistaPrevia && <img className="vista-previa" src={vistaPrevia} alt="Foto seleccionada" />}
    </div>
  )
}
