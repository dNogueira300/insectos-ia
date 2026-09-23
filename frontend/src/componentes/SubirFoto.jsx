import { useState } from 'react'

export default function SubirFoto({ alSeleccionar, ocupado }) {
  const [vistaPrevia, setVistaPrevia] = useState(null)

  function manejar(evento) {
    const archivo = evento.target.files?.[0]
    if (!archivo) return
    setVistaPrevia(URL.createObjectURL(archivo))
    alSeleccionar(archivo)
  }

  return (
    <div className="subir">
      <label className="boton">
        {ocupado ? 'Identificando…' : 'Elegir foto del insecto'}
        <input type="file" accept="image/*" onChange={manejar} disabled={ocupado} hidden />
      </label>
      {vistaPrevia && <img className="vista-previa" src={vistaPrevia} alt="Foto seleccionada" />}
    </div>
  )
}
