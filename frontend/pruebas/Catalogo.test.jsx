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

describe('Catalogo: tres familias por orden con "Todos"', () => {
  const familia = (nombre) => ({
    id: `familia-${nombre}`, tipo: 'familia', nombre, nombre_comun: '', orden: 'Coleoptera',
    provisional: false, f1: 0.9, fotos_entrenamiento: 100, foto,
  })
  const GRANDE = {
    ...CATALOGO,
    clases: [...['Fam1', 'Fam2', 'Fam3', 'Fam4', 'Fam5'].map(familia), CATALOGO.clases[2]],
  }
  const visibles = () => [...document.querySelectorAll('[id^="familia-"]')].map((e) => e.id)

  beforeEach(() => {
    obtenerResumen.mockResolvedValue({ por_orden: [] })
    window.location.hash = ''
  })

  it('muestra 3 por orden y "Ver más" despliega el resto; "Ver menos" lo vuelve a plegar', () => {
    render(<Catalogo catalogo={GRANDE} error="" />)
    expect(visibles()).toEqual(['familia-Fam1', 'familia-Fam2', 'familia-Fam3'])
    const boton = screen.getByRole('button', { name: 'Ver 2 familias más de Coleoptera' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(boton)
    expect(visibles()).toHaveLength(5)
    const menos = screen.getByRole('button', { name: 'Ver menos de Coleoptera' })
    expect(menos).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(menos)
    expect(visibles()).toHaveLength(3)
  })

  it('un orden con 3 o menos no ofrece "Ver más"', () => {
    render(<Catalogo catalogo={GRANDE} error="" />)
    expect(screen.queryByRole('button', { name: /de Mantodea/ })).toBeNull()
  })

  it('al elegir un orden o buscar se ven todas las coincidencias', () => {
    render(<Catalogo catalogo={GRANDE} error="" />)
    fireEvent.click(screen.getByRole('button', { name: 'Coleoptera' }))
    expect(visibles()).toHaveLength(5)
    expect(screen.queryByRole('button', { name: /familias más/ })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Todos' }))
    fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'fam' } })
    expect(visibles()).toHaveLength(5)
  })

  it('el enlace a una familia oculta despliega su orden para que la tarjeta exista', () => {
    window.location.hash = '#familia-Fam5'
    render(<Catalogo catalogo={GRANDE} error="" />)
    expect(document.getElementById('familia-Fam5')).not.toBeNull()
    expect(screen.getByRole('button', { name: 'Ver menos de Coleoptera' })).toBeInTheDocument()
  })

  it('con una sola familia oculta lo dice en singular', () => {
    const cuatro = { ...GRANDE, clases: GRANDE.clases.filter((c) => c.nombre !== 'Fam5') }
    render(<Catalogo catalogo={cuatro} error="" />)
    expect(screen.getByRole('button', { name: 'Ver 1 familia más de Coleoptera' })).toBeInTheDocument()
  })
})
