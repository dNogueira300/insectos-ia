// Cliente HTTP del backend. Es el único lugar del frontend que sabe de rutas.
export const BASE_API = import.meta.env.VITE_API ?? 'http://127.0.0.1:8000'

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
  }
}

async function pedir(ruta, opciones = {}) {
  let respuesta
  try {
    respuesta = await fetch(`${BASE_API}${ruta}`, opciones)
  } catch {
    throw new ErrorApi('No se pudo conectar con el servidor. ¿Está encendido?', 0)
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
  return pedir('/predecir', { method: 'POST', body: cuerpo })
}

export function obtenerTaxon(orden, familia = '') {
  const consulta = familia ? `?familia=${encodeURIComponent(familia)}` : ''
  return pedir(`/taxon/${encodeURIComponent(orden)}${consulta}`)
}
