import { act, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/api.js', () => ({ obtenerClases: vi.fn(), obtenerTaxon: vi.fn() }))

import { obtenerClases, obtenerTaxon } from '../src/api.js'
import Explorador from '../src/componentes/Explorador.jsx'

// Respuestas que se resuelven cuando la prueba lo decide.
function pendientes() {
  const porOrden = {}
  obtenerTaxon.mockImplementation(
    (orden) =>
      new Promise((resolver) => {
        porOrden[orden] = (nombre) =>
          resolver({ fichas: [{ ID: `ID-${orden}`, Nombre_comun: nombre }] })
      }),
  )
  return porOrden
}

async function montar() {
  render(<Explorador />)
  return screen.findByRole('combobox')
}

describe('Explorador', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    obtenerClases.mockResolvedValue({ ordenes: ['OrdenA', 'OrdenB'] })
  })

  it('una respuesta tardía del orden anterior no pisa la del actual', async () => {
    const responder = pendientes()
    const selector = await montar()

    fireEvent.change(selector, { target: { value: 'OrdenA' } })
    fireEvent.change(selector, { target: { value: 'OrdenB' } })
    await act(async () => responder.OrdenB('bicho B'))
    await act(async () => responder.OrdenA('bicho A'))

    expect(screen.getByText('bicho B')).toBeInTheDocument()
    expect(screen.queryByText('bicho A')).not.toBeInTheDocument()
  })

  it('al cambiar de orden no deja a la vista las fichas del anterior', async () => {
    const responder = pendientes()
    const selector = await montar()

    fireEvent.change(selector, { target: { value: 'OrdenA' } })
    await act(async () => responder.OrdenA('bicho A'))
    expect(screen.getByText('bicho A')).toBeInTheDocument()

    fireEvent.change(selector, { target: { value: 'OrdenB' } })
    expect(screen.queryByText('bicho A')).not.toBeInTheDocument()
  })
})
