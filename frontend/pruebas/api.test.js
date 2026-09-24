import { afterEach, describe, expect, it, vi } from 'vitest'
import { ErrorApi, obtenerClases, obtenerSalud, obtenerTaxon, predecir } from '../src/api.js'

function respuesta(cuerpo, ok = true, estado = 200) {
  return Promise.resolve({ ok, status: estado, json: () => Promise.resolve(cuerpo) })
}

afterEach(() => vi.restoreAllMocks())

describe('cliente de la API', () => {
  it('obtiene el estado de salud', async () => {
    global.fetch = vi.fn(() => respuesta({ estado: 'ok' }))
    expect(await obtenerSalud()).toEqual({ estado: 'ok' })
  })

  it('obtiene las clases', async () => {
    global.fetch = vi.fn(() => respuesta({ ordenes: ['Coleoptera'] }))
    const clases = await obtenerClases()
    expect(clases.ordenes).toEqual(['Coleoptera'])
  })

  it('envía la imagen como multipart con el campo "archivo"', async () => {
    global.fetch = vi.fn(() => respuesta({ orden: 'Coleoptera' }))
    const archivo = new File(['x'], 'insecto.jpg', { type: 'image/jpeg' })
    await predecir(archivo)

    const [, opciones] = global.fetch.mock.calls[0]
    expect(opciones.method).toBe('POST')
    expect(opciones.body).toBeInstanceOf(FormData)
    expect(opciones.body.get('archivo')).toBe(archivo)
  })

  it('lanza ErrorApi con el estado cuando la respuesta falla', async () => {
    global.fetch = vi.fn(() => respuesta({ detail: 'el archivo no es una imagen válida' }, false, 400))
    const archivo = new File(['x'], 'malo.txt', { type: 'text/plain' })
    await expect(predecir(archivo)).rejects.toThrow(ErrorApi)
  })

  it('el mensaje del error viene del backend', async () => {
    global.fetch = vi.fn(() => respuesta({ detail: 'el archivo no es una imagen válida' }, false, 400))
    try {
      await predecir(new File(['x'], 'malo.txt'))
      throw new Error('debió lanzar')
    } catch (error) {
      expect(error.message).toContain('imagen')
      expect(error.estado).toBe(400)
    }
  })

  it('avisa cuando el servidor no responde', async () => {
    global.fetch = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    await expect(obtenerSalud()).rejects.toThrow(/servidor/i)
  })

  it('pasa la familia como parámetro de consulta', async () => {
    global.fetch = vi.fn(() => respuesta({ fichas: [] }))
    await obtenerTaxon('Coleoptera', 'Curculionidae')
    expect(global.fetch.mock.calls[0][0]).toContain('familia=Curculionidae')
  })

  it('omite la familia cuando no se pasa', async () => {
    global.fetch = vi.fn(() => respuesta({ fichas: [] }))
    await obtenerTaxon('Coleoptera')
    expect(global.fetch.mock.calls[0][0]).not.toContain('familia=')
  })
})

describe('dirección del backend', () => {
  it('en producción usa rutas relativas: la página la sirve el mismo backend', async () => {
    // Abrirla como localhost:8000 o desde un teléfono no debe apuntar a 127.0.0.1.
    const { resolverBaseApi } = await import('../src/api.js')
    expect(resolverBaseApi({ DEV: false })).toBe('')
  })

  it('en desarrollo apunta al backend del puerto 8000', async () => {
    const { resolverBaseApi } = await import('../src/api.js')
    expect(resolverBaseApi({ DEV: true })).toBe('http://127.0.0.1:8000')
  })

  it('VITE_API tiene prioridad', async () => {
    const { resolverBaseApi } = await import('../src/api.js')
    expect(resolverBaseApi({ DEV: false, VITE_API: 'http://otro:9000' })).toBe('http://otro:9000')
  })
})
