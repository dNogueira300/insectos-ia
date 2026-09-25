import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/api.js', () => ({ predecir: vi.fn() }))
vi.mock('../src/compartido/datos.js', () => ({
  cargarDemostracion: vi.fn(),
  archivoDesdeRuta: vi.fn(),
}))

import { predecir } from '../src/compartido/api.js'
import { archivoDesdeRuta, cargarDemostracion } from '../src/compartido/datos.js'
import Identificar from '../src/paginas/identificar/Identificar.jsx'

const AFIRMADA = {
  orden: 'Hymenoptera', confianza_orden: 0.99, familia: 'Apidae', confianza_familia: 0.98,
  familia_incierta: false, top_familias: [{ familia: 'Apidae', confianza: 0.98 }],
  fichas: [{ ID: 'INS-0003', Nombre_comun: 'abeja melífera', Importancia_economica: 'Benéfico - polinizador' }],
}
const INCIERTA = {
  orden: 'Odonata', confianza_orden: 0.91, familia: 'Gomphidae', confianza_familia: 0.53,
  familia_incierta: true,
  top_familias: [{ familia: 'Gomphidae', confianza: 0.53 }, { familia: 'Coenagrionidae', confianza: 0.43 }],
  fichas: [],
}
const EJEMPLO = {
  archivo: '/catalogo/demo/abeja.webp', credito: '(c) Ana', licencia: 'cc-by',
  real: { orden: 'Hymenoptera', familia: 'Apidae' },
}
const foto = () => new File(['x'], 'insecto.jpg', { type: 'image/jpeg' })

async function montar() {
  const vista = render(<Identificar />)
  await screen.findByText('Probar con un ejemplo')
  return vista
}

describe('Identificar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cargarDemostracion.mockResolvedValue({ ejemplos: [EJEMPLO] })
    URL.createObjectURL = vi.fn(() => 'blob:1')
    URL.revokeObjectURL = vi.fn()
  })

  it('en estado vacío muestra consejos abiertos y ejemplos', async () => {
    const { container } = await montar()
    expect(container.querySelector('details.consejos')).toHaveAttribute('open')
    expect(screen.getByText(/Aquí aparecerá/)).toBeInTheDocument()
  })

  it('identifica una foto elegida y muestra resultado y ficha', async () => {
    predecir.mockResolvedValue(AFIRMADA)
    const { container } = await montar()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [foto()] } })
    // "Apidae" también es el rótulo del botón de ejemplo: se busca por la ficha.
    expect(await screen.findByText('abeja melífera')).toBeInTheDocument()
    expect(screen.getByText('Afirmada')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Información biológica' })).toBeInTheDocument()
    expect(container.querySelector('details.consejos')).not.toHaveAttribute('open')
  })

  it('con familia incierta titula las fichas como registros del orden', async () => {
    predecir.mockResolvedValue({ ...INCIERTA, fichas: [{ ID: '9', Nombre_comun: 'libélula' }] })
    const { container } = await montar()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [foto()] } })
    expect(await screen.findByRole('heading', { name: 'Registros del orden Odonata en la base' })).toBeInTheDocument()
  })

  it('muestra el error del backend y reintenta con la misma foto', async () => {
    predecir.mockRejectedValueOnce(new Error('la foto pesa más de 20 MB: usa una más liviana'))
    predecir.mockResolvedValueOnce(AFIRMADA)
    const { container } = await montar()
    const archivo = foto()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [archivo] } })
    expect(await screen.findByRole('alert')).toHaveTextContent('20 MB')
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('abeja melífera')).toBeInTheDocument()
    expect(predecir).toHaveBeenLastCalledWith(archivo)
  })

  it('un ejemplo se envía de verdad a la API', async () => {
    const archivo = foto()
    archivoDesdeRuta.mockResolvedValue(archivo)
    predecir.mockResolvedValue(AFIRMADA)
    await montar()
    fireEvent.click(screen.getByRole('button', { name: /Apidae/ }))
    expect(await screen.findByText('abeja melífera')).toBeInTheDocument()
    expect(archivoDesdeRuta).toHaveBeenCalledWith('/catalogo/demo/abeja.webp', 'abeja.webp')
    expect(predecir).toHaveBeenCalledWith(archivo)
  })

  it('si la foto de ejemplo no carga, lo dice y no queda identificando', async () => {
    archivoDesdeRuta.mockRejectedValue(new Error('No se pudo cargar la foto de ejemplo.'))
    await montar()
    fireEvent.click(screen.getByRole('button', { name: /Apidae/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('foto de ejemplo')
    expect(screen.queryByText('Identificando…')).not.toBeInTheDocument()
  })

  it('"Identificar otra foto" vuelve al estado vacío', async () => {
    predecir.mockResolvedValue(AFIRMADA)
    const { container } = await montar()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [foto()] } })
    fireEvent.click(await screen.findByRole('button', { name: 'Identificar otra foto' }))
    expect(screen.getByText(/Aquí aparecerá/)).toBeInTheDocument()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:1')
  })

  it('sin demostración disponible la página funciona igual', async () => {
    cargarDemostracion.mockRejectedValue(new Error('No se encontró el contenido del catálogo.'))
    render(<Identificar />)
    await act(async () => {})
    expect(screen.queryByText('Probar con un ejemplo')).not.toBeInTheDocument()
    expect(screen.getByText('Elegir foto')).toBeInTheDocument()
  })
})
