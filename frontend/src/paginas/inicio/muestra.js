// Dos filas del catálogo: 8 tarjetas con cuatro columnas. Con menos columnas,
// el CSS oculta las que pasarían de la segunda fila.
const EN_VISTA = 8

// Una clase de cada orden, para que la muestra sea variada; si hay menos
// órdenes que lugares, se completa con las clases siguientes.
export function elegirMuestra(clases, cantidad = EN_VISTA) {
  const vistos = new Set()
  const primeras = clases.filter((c) => !vistos.has(c.orden) && vistos.add(c.orden))
  const resto = clases.filter((c) => !primeras.includes(c))
  return [...primeras, ...resto].slice(0, cantidad)
}
