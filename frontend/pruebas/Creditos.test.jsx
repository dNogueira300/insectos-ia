import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Creditos from '../src/paginas/creditos/Creditos.jsx'
import { CREDITOS } from '../src/paginas/creditos/creditos.js'

describe('Créditos', () => {
  it('nombra al grupo, a la docente y a los desarrolladores', () => {
    render(<Creditos />)
    const seccion = screen.getByRole('heading', { level: 1, name: 'Créditos' }).closest('section')
    expect(seccion).toHaveTextContent('(INAAM)')
    expect(seccion).toHaveTextContent('Aldi Guerra Teixeira')
    expect(within(seccion).getByText('Elias Daniel Nogueira Del Aguila')).toBeInTheDocument()
    expect(within(seccion).getByText('Dan Willy Chasnamote Navarro')).toBeInTheDocument()
  })

  it('lista a los estudiantes que recolectaron y fotografiaron los ejemplares', () => {
    render(<Creditos />)
    expect(screen.getByText('Antero Valentín Acho Vásquez')).toBeInTheDocument()
    expect(screen.getByText('Rudber Ramiro Mori Dávila')).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(CREDITOS.recolectores.length)
    expect(CREDITOS.recolectores.length).toBeGreaterThan(90)
    expect(screen.queryByText(/se agregarán pronto/)).not.toBeInTheDocument()
  })

  it('sin recolectores, avisa que sus nombres se agregarán', () => {
    render(<Creditos creditos={{ ...CREDITOS, recolectores: [] }} />)
    expect(screen.getByText(/se agregarán pronto/)).toBeInTheDocument()
  })

  it('con recolectores, los lista y quita el aviso', () => {
    render(<Creditos creditos={{ ...CREDITOS, recolectores: ['Ana Ríos', 'Luis Paz'] }} />)
    expect(screen.getAllByRole('listitem').map((li) => li.textContent)).toEqual(['Ana Ríos', 'Luis Paz'])
    expect(screen.queryByText(/se agregarán pronto/)).not.toBeInTheDocument()
  })
})
