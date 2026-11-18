import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/api.js', () => ({
  obtenerTaxon: vi.fn(),
  obtenerResumen: vi.fn(() => Promise.resolve({ por_orden: [] })),
}))

import { elegirMuestra } from '../src/paginas/inicio/muestra.js'
import VistaCatalogo from '../src/paginas/inicio/VistaCatalogo.jsx'

const foto = { archivo: '/x.webp', ancho: 640, alto: 480, credito: '', licencia: 'cc0', url_origen: '' }
const clase = (orden, nombre) => ({
  id: `familia-${nombre}`, tipo: 'familia', nombre, nombre_comun: '', orden, provisional: false, f1: 0.9, foto,
})

describe('elegirMuestra', () => {
  it('toma primero una clase de cada orden y completa con las siguientes', () => {
    const clases = [clase('A', 'A1'), clase('A', 'A2'), clase('B', 'B1'), clase('C', 'C1'), clase('A', 'A3')]
    expect(elegirMuestra(clases, 4).map((c) => c.nombre)).toEqual(['A1', 'B1', 'C1', 'A2'])
  })

  it('nunca pasa de la cantidad pedida', () => {
    const clases = Array.from({ length: 20 }, (_, i) => clase(`O${i}`, `F${i}`))
    expect(elegirMuestra(clases)).toHaveLength(8)
  })
})

describe('VistaCatalogo', () => {
  it('muestra a lo más ocho tarjetas y el enlace al catálogo completo', () => {
    const clases = Array.from({ length: 12 }, (_, i) => clase(`O${i}`, `F${i}`))
    render(<VistaCatalogo catalogo={{ ordenes: [], clases }} error="" />)
    expect(document.querySelectorAll('.tarjeta')).toHaveLength(8)
    expect(screen.getByRole('link', { name: 'Ver catálogo completo' })).toHaveAttribute('href', '/catalogo/')
  })
})
