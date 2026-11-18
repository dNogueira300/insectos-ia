import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/api.js', () => ({ obtenerTaxon: vi.fn() }))
import { obtenerTaxon } from '../src/compartido/api.js'
import PaginaRegistros from '../src/paginas/registros/PaginaRegistros.jsx'

const fichas = Array.from({ length: 15 }, (_, i) => ({ ID: `R${i}`, Nombre_comun: `gorgojo ${i}`, Importancia_economica: 'Plaga', Cultivo_asociado: 'Plátano' }))

function abrir(busqueda) {
  window.history.pushState({}, '', `/registros/${busqueda}`)
  return render(<PaginaRegistros />)
}

describe('PaginaRegistros', () => {
  beforeEach(() => obtenerTaxon.mockResolvedValue({ fichas }))
  afterEach(() => vi.clearAllMocks())

  it('pide los registros de la familia indicada en la dirección', async () => {
    abrir('?orden=Coleoptera&familia=Curculionidae')
    expect(await screen.findByRole('heading', { level: 1, name: 'Registros de Curculionidae' })).toBeInTheDocument()
    expect(obtenerTaxon).toHaveBeenCalledWith('Coleoptera', 'Curculionidae')
  })

  it('explica de dónde salen los registros', async () => {
    abrir('?orden=Coleoptera&familia=Curculionidae')
    await screen.findByRole('heading', { level: 1 })
    expect(screen.getByText(/Entomología General y Aplicada/)).toBeInTheDocument()
    expect(screen.getByText(/no son la identificación de tu foto/)).toBeInTheDocument()
  })

  it('muestra el resumen y la lista completa de registros, por partes', async () => {
    abrir('?orden=Coleoptera&familia=Curculionidae')
    expect(await screen.findByText(/Resumen de 15 registros/)).toBeInTheDocument()
    expect(screen.getAllByText(/^gorgojo \d+$/)).toHaveLength(12)
    expect(screen.getByRole('button', { name: 'Ver 3 fichas más' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Ver los 15 registros/ })).toBeNull()
  })

  it('un orden sin familias se pide solo por orden', async () => {
    abrir('?orden=Mantodea')
    expect(await screen.findByRole('heading', { level: 1, name: 'Registros de Mantodea' })).toBeInTheDocument()
    expect(obtenerTaxon).toHaveBeenCalledWith('Mantodea', '')
  })

  it('sin taxón en la dirección, lleva al catálogo', () => {
    abrir('')
    expect(screen.getByRole('link', { name: 'Ir al catálogo' })).toHaveAttribute('href', '/catalogo/')
    expect(obtenerTaxon).not.toHaveBeenCalled()
  })
})
