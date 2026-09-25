import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/api.js', () => ({ obtenerTaxon: vi.fn(), obtenerResumen: vi.fn() }))

import { obtenerResumen, obtenerTaxon } from '../src/compartido/api.js'
import Catalogo from '../src/paginas/inicio/Catalogo.jsx'

const foto = { archivo: '/catalogo/fotos/x.webp', ancho: 640, alto: 480, credito: '', licencia: 'cc-by', url_origen: '' }
const CATALOGO = {
  corrida: 'v4',
  metricas: {},
  ordenes: [
    { nombre: 'Coleoptera', nombre_comun: 'escarabajos', tiene_familias: true },
    { nombre: 'Mantodea', nombre_comun: 'mantis', tiene_familias: false },
  ],
  clases: [
    { id: 'familia-Curculionidae', tipo: 'familia', nombre: 'Curculionidae', nombre_comun: 'gorgojos',
      orden: 'Coleoptera', provisional: false, f1: 0.92, fotos_entrenamiento: 600,
      foto: { ...foto, credito: '(c) Ana' } },
    { id: 'familia-Coccinellidae', tipo: 'familia', nombre: 'Coccinellidae', nombre_comun: 'mariquitas',
      orden: 'Coleoptera', provisional: true, f1: 0.95, fotos_entrenamiento: 580,
      foto: { ...foto, credito: 'Autor no registrado' } },
    { id: 'orden-Mantodea', tipo: 'orden', nombre: 'Mantodea', nombre_comun: 'mantis',
      orden: 'Mantodea', provisional: false, f1: 0.87, fotos_entrenamiento: 817, foto },
  ],
}

describe('Catalogo', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Por defecto la base tiene fichas en los dos órdenes del catálogo de prueba.
    obtenerResumen.mockResolvedValue({ por_orden: [
      { orden: 'Coleoptera', registros: 2 }, { orden: 'Mantodea', registros: 1 },
    ] })
  })

  it('agrupa por orden y muestra cada clase con su F1 y el crédito de la foto', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    const tarjeta = document.getElementById('familia-Curculionidae')
    expect(within(tarjeta).getByText('gorgojos')).toBeInTheDocument()
    expect(within(tarjeta).getByText('92 %')).toBeInTheDocument()
    expect(within(tarjeta).getByText(/\(c\) Ana · CC BY/)).toBeInTheDocument()
  })

  it('marca las familias provisionales', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    expect(within(document.getElementById('familia-Coccinellidae')).getByText('Provisional')).toBeInTheDocument()
    expect(within(document.getElementById('familia-Curculionidae')).queryByText('Provisional')).not.toBeInTheDocument()
  })

  it('un orden sin familias dice que se identifica solo hasta orden', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    expect(within(document.getElementById('orden-Mantodea')).getByText(/solo hasta orden/i)).toBeInTheDocument()
  })

  it('filtra por orden', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.click(screen.getByRole('button', { name: 'Mantodea' }))
    expect(document.getElementById('familia-Curculionidae')).toBeNull()
    expect(document.getElementById('orden-Mantodea')).not.toBeNull()
    expect(screen.getByRole('button', { name: 'Mantodea' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('busca por nombre común sin importar tildes ni mayúsculas', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'MARIQUÍTAS' } })
    expect(document.getElementById('familia-Coccinellidae')).not.toBeNull()
    expect(document.getElementById('familia-Curculionidae')).toBeNull()
  })

  it('avisa cuando la búsqueda no encuentra nada', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'zzz' } })
    expect(screen.getByText(/no hay clases que coincidan/i)).toBeInTheDocument()
  })

  it('abre las fichas de la familia y se cierra con Escape', async () => {
    obtenerTaxon.mockResolvedValue({ fichas: [{ ID: '1', Nombre_comun: 'gorgojo del plátano' }] })
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.click(within(document.getElementById('familia-Curculionidae')).getByRole('button', { name: 'Ver fichas' }))
    expect(await screen.findByText('gorgojo del plátano')).toBeInTheDocument()
    expect(obtenerTaxon).toHaveBeenCalledWith('Coleoptera', 'Curculionidae')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('las fichas de un orden sin familias se piden por orden', async () => {
    obtenerTaxon.mockResolvedValue({ fichas: [] })
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.click(within(document.getElementById('orden-Mantodea')).getByRole('button', { name: 'Ver fichas' }))
    expect(await screen.findByText('Aún no hay fichas de este orden en la base.')).toBeInTheDocument()
    expect(obtenerTaxon).toHaveBeenCalledWith('Mantodea', '')
  })

  it('si el catálogo no carga, lo explica', () => {
    render(<Catalogo catalogo={null} error="No se encontró el contenido del catálogo." />)
    expect(screen.getByRole('alert')).toHaveTextContent('No se encontró')
  })

  it('con el panel abierto, Tab no se escapa a la página de atrás', async () => {
    obtenerTaxon.mockResolvedValue({ fichas: [{ ID: '1', Nombre_comun: 'gorgojo del plátano' }] })
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.click(within(document.getElementById('familia-Curculionidae')).getByRole('button', { name: 'Ver fichas' }))
    await screen.findByText('gorgojo del plátano')
    const cerrar = screen.getByRole('button', { name: 'Cerrar' })
    expect(cerrar).toHaveFocus()
    // fireEvent devuelve false cuando el panel cancela el Tab para retener el foco.
    expect(fireEvent.keyDown(cerrar, { key: 'Tab' })).toBe(false)
    expect(fireEvent.keyDown(cerrar, { key: 'Tab', shiftKey: true })).toBe(false)
    expect(cerrar).toHaveFocus()
  })

  it('sin registros del orden en la base, la tarjeta lo dice en vez de abrir un panel vacío', async () => {
    obtenerResumen.mockResolvedValue({ por_orden: [{ orden: 'Coleoptera', registros: 2 }] })
    render(<Catalogo catalogo={CATALOGO} error="" />)
    const mantis = document.getElementById('orden-Mantodea')
    expect(await within(mantis).findByText('Sin fichas en la base todavía.')).toBeInTheDocument()
    expect(within(mantis).queryByRole('button', { name: 'Ver fichas' })).toBeNull()
    const gorgojos = document.getElementById('familia-Curculionidae')
    expect(within(gorgojos).getByRole('button', { name: 'Ver fichas' })).toBeInTheDocument()
  })

  it('si el resumen no llega, todas las tarjetas conservan "Ver fichas"', async () => {
    obtenerResumen.mockRejectedValue(new Error('sin conexión'))
    render(<Catalogo catalogo={CATALOGO} error="" />)
    await Promise.resolve()
    expect(screen.getAllByRole('button', { name: 'Ver fichas' })).toHaveLength(3)
  })

  it('cada orden con familias tiene su ancla, para el enlace del resultado incierto', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    const coleoptera = document.getElementById('orden-Coleoptera')
    expect(coleoptera).not.toBeNull()
    expect(coleoptera).toContainElement(document.getElementById('familia-Curculionidae'))
    // Los órdenes sin familias ya tienen ancla en su tarjeta: no se repite el id.
    expect(document.querySelectorAll('[id="orden-Mantodea"]')).toHaveLength(1)
  })
})
