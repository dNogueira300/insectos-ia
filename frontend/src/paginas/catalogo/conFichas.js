import { useEffect, useState } from 'react'
import { obtenerResumen } from '../../compartido/api.js'

// Órdenes con registros en la base, consultados en vivo: la base crece con el
// Excel de Agronomía y un conteo guardado en catalogo.json quedaría viejo. Si
// no se puede consultar, devuelve null y todas las tarjetas conservan "Ver fichas".
export function useOrdenesConFichas() {
  const [conFichas, setConFichas] = useState(null)

  useEffect(() => {
    let vigente = true
    obtenerResumen()
      .then(({ por_orden }) => {
        if (vigente) setConFichas(new Set(por_orden.filter((o) => o.registros > 0).map((o) => o.orden)))
      })
      .catch(() => {})
    return () => {
      vigente = false
    }
  }, [])

  return conFichas
}
