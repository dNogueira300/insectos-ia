import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/datos.js', () => ({ cargarCatalogo: vi.fn() }))
vi.mock('../src/compartido/api.js', () => ({
  obtenerTaxon: vi.fn(),
  obtenerResumen: vi.fn(() => Promise.resolve({ por_orden: [] })),
}))

import { cargarCatalogo } from '../src/compartido/datos.js'
import PaginaCatalogo from '../src/paginas/catalogo/PaginaCatalogo.jsx'
import PaginaCreditos from '../src/paginas/creditos/PaginaCreditos.jsx'

describe('Páginas propias', () => {
  it('el catálogo es una página con su título, marcada en la cabecera', async () => {
    cargarCatalogo.mockResolvedValue({ corrida: 'v4', metricas: {}, ordenes: [], clases: [] })
    render(<PaginaCatalogo />)
    expect(screen.getByRole('heading', { level: 1, name: 'Catálogo de familias' })).toBeInTheDocument()
    expect(await screen.findByLabelText('Buscar')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Catálogo' })[0]).toHaveAttribute('aria-current', 'page')
  })

  it('los créditos son una página con su título, marcada en la cabecera', () => {
    render(<PaginaCreditos />)
    expect(screen.getByRole('heading', { level: 1, name: 'Créditos' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Créditos' })[0]).toHaveAttribute('aria-current', 'page')
  })
})
