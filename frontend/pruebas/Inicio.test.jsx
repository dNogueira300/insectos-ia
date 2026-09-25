import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/datos.js', () => ({ cargarCatalogo: vi.fn(), cargarDemostracion: vi.fn() }))
vi.mock('../src/compartido/api.js', () => ({
  obtenerTaxon: vi.fn(),
  obtenerResumen: vi.fn(() => Promise.resolve({ por_orden: [] })),
}))

import { cargarCatalogo, cargarDemostracion } from '../src/compartido/datos.js'
import Inicio from '../src/paginas/inicio/Inicio.jsx'

const PRED = (familia, conf, incierta) => ({
  orden: 'Hymenoptera', confianza_orden: 0.99, familia, confianza_familia: conf,
  familia_incierta: incierta, top_familias: [{ familia, confianza: conf }],
})
const DEMO = {
  principal: { archivo: '/catalogo/demo/a.webp', credito: '(c) Ana', licencia: 'cc-by',
    real: { orden: 'Hymenoptera', familia: 'Apidae' }, prediccion: PRED('Apidae', 0.98, false) },
  incierto: { archivo: '/catalogo/demo/b.webp', credito: '(c) Luis', licencia: 'cc0',
    real: { orden: 'Hymenoptera', familia: 'Vespidae' }, prediccion: PRED('Vespidae', 0.52, true) },
  ejemplos: [],
}
const CATALOGO = {
  corrida: 'v4_convnext_t_288',
  metricas: { n_prueba: 5165, exactitud_familia: 0.9216, top3_familia: 0.958, f1_orden: 0.935,
    f1_familia: 0.921, umbral: 0.7, responde: 0.94, acierta_cuando_responde: 0.955 },
  ordenes: [], clases: [],
}

describe('Inicio', () => {
  beforeEach(() => {
    cargarCatalogo.mockResolvedValue(CATALOGO)
    cargarDemostracion.mockResolvedValue(DEMO)
  })

  it('la portada lleva a la herramienta', async () => {
    render(<Inicio />)
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent(/orden y la familia/)
    const acciones = screen.getAllByRole('link', { name: 'Identificar un insecto' })
    expect(acciones.every((a) => a.getAttribute('href') === '/identificar/')).toBe(true)
  })

  it('la demostración es un resultado real rotulado, con el crédito de la foto', async () => {
    render(<Inicio />)
    expect(await screen.findByText('Resultado real del modelo con esta foto')).toBeInTheDocument()
    expect(screen.getByText(/\(c\) Ana/).closest('.credito')).toHaveTextContent('Foto: (c) Ana · CC BY')
  })

  it('cómo funciona muestra un caso real en que no afirma la familia', async () => {
    render(<Inicio />)
    expect(await screen.findByText(/prefiere no afirmar la familia/)).toBeInTheDocument()
    expect(screen.getByText(/no se puede determinar la familia/i)).toBeInTheDocument()
  })

  it('las cifras salen del catálogo y aclaran que son de fotos de catálogo', async () => {
    render(<Inicio />)
    const bloque = (await screen.findByRole('heading', { name: 'Qué tan bien funciona' })).closest('section')
    // Frases con la cifra dentro, no la plantilla de cifra grande con rótulo.
    expect(bloque).toHaveTextContent('Acierta la familia en el 92 % de las fotos de prueba.')
    expect(bloque).toHaveTextContent('acierta el 95.5 %')
    expect(bloque).toHaveTextContent('responde en el 94 % de los casos')
    expect(bloque).toHaveTextContent('entre sus tres primeras opciones el 96 %')
    expect(screen.getByText(/evaluación con fotos de campo está pendiente/i)).toBeInTheDocument()
  })

  it('sin catálogo ni demostración la portada sigue en pie', async () => {
    cargarCatalogo.mockRejectedValue(new Error('No se encontró el contenido del catálogo.'))
    cargarDemostracion.mockRejectedValue(new Error('x'))
    render(<Inicio />)
    expect(await screen.findByRole('alert')).toHaveTextContent('No se encontró')
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })

  it('el caso incierto dice, con los datos, que afirmar habría sido un error', async () => {
    const incierto = {
      ...DEMO.incierto,
      real: { orden: 'Diptera', familia: 'Tephritidae' },
      prediccion: { ...PRED('Anthomyiidae', 0.65, true), orden: 'Diptera',
        top_familias: [{ familia: 'Anthomyiidae', confianza: 0.65 }, { familia: 'Tephritidae', confianza: 0.28 }] },
    }
    cargarDemostracion.mockResolvedValue({ ...DEMO, incierto })
    render(<Inicio />)
    expect(await screen.findByText(/La familia correcta era/)).toHaveTextContent(
      'La familia correcta era Tephritidae, su segunda candidata: afirmar Anthomyiidae habría sido un error.',
    )
  })
})
