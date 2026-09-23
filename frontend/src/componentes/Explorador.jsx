import { useEffect, useState } from 'react'
import { obtenerClases, obtenerTaxon } from '../api.js'
import Ficha from './Ficha.jsx'

export default function Explorador() {
  const [ordenes, setOrdenes] = useState([])
  const [orden, setOrden] = useState('')
  const [fichas, setFichas] = useState([])

  useEffect(() => {
    obtenerClases()
      .then((clases) => setOrdenes(clases.ordenes))
      .catch(() => setOrdenes([]))
  }, [])

  useEffect(() => {
    if (!orden) return
    obtenerTaxon(orden)
      .then((datos) => setFichas(datos.fichas))
      .catch(() => setFichas([]))
  }, [orden])

  if (ordenes.length === 0) return null

  return (
    <section className="explorador">
      <h2>Explorar la base de datos</h2>
      <select value={orden} onChange={(e) => setOrden(e.target.value)}>
        <option value="">Elegir un orden…</option>
        {ordenes.map((nombre) => (
          <option key={nombre} value={nombre}>
            {nombre}
          </option>
        ))}
      </select>
      {orden && <Ficha fichas={fichas} />}
    </section>
  )
}
