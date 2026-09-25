// Contenido generado por pipeline/catalogo_web.py y servido como archivo estático
// junto a la página. No pasa por la API: mismo origen en producción y en Vite.
export const RUTA_CATALOGO = '/catalogo/catalogo.json'
export const RUTA_DEMOSTRACION = '/catalogo/demostracion.json'

async function leerJson(ruta) {
  let respuesta
  try {
    respuesta = await fetch(ruta)
  } catch {
    throw new Error('No se pudo cargar el contenido. ¿Está encendido el servidor?')
  }
  if (!respuesta.ok) throw new Error('No se encontró el contenido del catálogo.')
  return respuesta.json()
}

export const cargarCatalogo = () => leerJson(RUTA_CATALOGO)
export const cargarDemostracion = () => leerJson(RUTA_DEMOSTRACION)

// Convierte una foto de ejemplo publicada en un File, para enviarla a /predecir.
export async function archivoDesdeRuta(ruta, nombre) {
  let respuesta
  try {
    respuesta = await fetch(ruta)
  } catch {
    throw new Error('No se pudo cargar la foto de ejemplo.')
  }
  if (!respuesta.ok) throw new Error('No se pudo cargar la foto de ejemplo.')
  const blob = await respuesta.blob()
  return new File([blob], nombre, { type: blob.type || 'image/webp' })
}
