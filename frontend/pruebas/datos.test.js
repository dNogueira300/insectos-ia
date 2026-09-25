import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  RUTA_CATALOGO,
  archivoDesdeRuta,
  cargarCatalogo,
  cargarDemostracion,
} from '../src/compartido/datos.js'

afterEach(() => vi.restoreAllMocks())

describe('datos estáticos', () => {
  it('lee el catálogo desde public/, no desde la API', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ clases: [] }) }))
    await cargarCatalogo()
    expect(global.fetch).toHaveBeenCalledWith(RUTA_CATALOGO)
    expect(RUTA_CATALOGO).toBe('/catalogo/catalogo.json')
  })

  it('explica cuando el catálogo no existe', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false, status: 404 }))
    await expect(cargarDemostracion()).rejects.toThrow(/no se encontró/i)
  })

  it('explica cuando el servidor no responde', async () => {
    global.fetch = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    await expect(cargarCatalogo()).rejects.toThrow(/servidor/i)
  })

  it('convierte una foto de ejemplo en un File', async () => {
    const blob = new Blob(['x'], { type: 'image/webp' })
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, blob: () => Promise.resolve(blob) }))
    const archivo = await archivoDesdeRuta('/catalogo/demo/a.webp', 'a.webp')
    expect(archivo).toBeInstanceOf(File)
    expect(archivo.name).toBe('a.webp')
    expect(archivo.type).toBe('image/webp')
  })

  it('avisa cuando la foto de ejemplo no carga', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false, status: 404 }))
    await expect(archivoDesdeRuta('/catalogo/demo/x.webp', 'x.webp')).rejects.toThrow(/foto de ejemplo/i)
  })
})
