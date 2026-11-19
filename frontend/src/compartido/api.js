// Cliente HTTP del backend. Es el único lugar del frontend que sabe de rutas.
// En producción la página la sirve el mismo backend: rutas relativas, así
// funciona igual abierta como localhost, 127.0.0.1 o desde otro equipo. Solo en
// desarrollo (Vite en 5173) hay que apuntar al backend del puerto 8000.
export function resolverBaseApi(entorno) {
  return entorno.VITE_API ?? (entorno.DEV ? 'http://127.0.0.1:8000' : '')
}

export const BASE_API = resolverBaseApi(import.meta.env)

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
  }
}

// Tope para una identificación. Publicado en internet, el servidor puede estar
// dormido: despertarlo y subir la foto con datos móviles toma decenas de
// segundos. Más que esto es un servidor colgado, y la página no debe quedarse
// girando para siempre.
export const LIMITE_PREDICCION_MS = 90_000

async function pedir(ruta, opciones = {}, limiteMs = 0) {
  const control = new AbortController()
  const temporizador = limiteMs ? setTimeout(() => control.abort(), limiteMs) : null
  let respuesta
  try {
    respuesta = await fetch(`${BASE_API}${ruta}`, { ...opciones, signal: control.signal })
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new ErrorApi('El servidor tardó demasiado en responder. Espere unos segundos y vuelva a intentarlo.', 0)
    }
    throw new ErrorApi('No se pudo conectar con el servidor. ¿Está encendido?', 0)
  } finally {
    clearTimeout(temporizador)
  }

  let cuerpo = {}
  try {
    cuerpo = await respuesta.json()
  } catch {
    cuerpo = {}
  }

  if (!respuesta.ok) {
    throw new ErrorApi(cuerpo.detail ?? 'Ocurrió un error inesperado.', respuesta.status)
  }
  return cuerpo
}

export function obtenerSalud() {
  return pedir('/salud')
}

export function obtenerClases() {
  return pedir('/clases')
}

export function predecir(archivo) {
  const cuerpo = new FormData()
  cuerpo.append('archivo', archivo)
  return pedir('/predecir', { method: 'POST', body: cuerpo }, LIMITE_PREDICCION_MS)
}

export function obtenerResumen() {
  return pedir('/resumen')
}

export function obtenerTaxon(orden, familia = '') {
  const consulta = familia ? `?familia=${encodeURIComponent(familia)}` : ''
  return pedir(`/taxon/${encodeURIComponent(orden)}${consulta}`)
}
