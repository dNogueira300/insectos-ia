import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ZonaFoto from '../src/paginas/identificar/ZonaFoto.jsx'

const foto = () => new File(['x'], 'insecto.jpg', { type: 'image/jpeg' })
const entradas = (container) => container.querySelectorAll('input[type="file"]')

afterEach(() => {
  vi.restoreAllMocks()
  delete window.matchMedia
})

describe('ZonaFoto', () => {
  it('entrega el archivo elegido', () => {
    const alSeleccionar = vi.fn()
    const { container } = render(<ZonaFoto alSeleccionar={alSeleccionar} ocupado={false} vistaPrevia={null} />)
    const archivo = foto()
    fireEvent.change(entradas(container)[0], { target: { files: [archivo] } })
    expect(alSeleccionar).toHaveBeenCalledWith(archivo)
  })

  it('acepta solo los formatos que el backend admite', () => {
    const { container } = render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    expect(entradas(container)[0]).toHaveAttribute('accept', 'image/jpeg,image/png,image/webp')
  })

  it('deja listo un selector nuevo para poder elegir otra vez la misma foto', () => {
    const { container } = render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    const antes = entradas(container)[0]
    fireEvent.change(antes, { target: { files: [foto()] } })
    expect(entradas(container)[0]).not.toBe(antes)
  })

  it('acepta una foto arrastrada', () => {
    const alSeleccionar = vi.fn()
    render(<ZonaFoto alSeleccionar={alSeleccionar} ocupado={false} vistaPrevia={null} />)
    const archivo = foto()
    fireEvent.drop(screen.getByText(/arrastra una foto/i), { dataTransfer: { files: [archivo] } })
    expect(alSeleccionar).toHaveBeenCalledWith(archivo)
  })

  it('no acepta fotos mientras identifica', () => {
    const alSeleccionar = vi.fn()
    const { container } = render(<ZonaFoto alSeleccionar={alSeleccionar} ocupado vistaPrevia="blob:1" />)
    expect(entradas(container)[0]).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent('Identificando…')
  })

  it('ofrece la cámara solo en pantallas táctiles', () => {
    window.matchMedia = vi.fn(() => ({ matches: true }))
    const { container } = render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    expect(screen.getByText('Tomar foto')).toBeInTheDocument()
    expect(entradas(container)[0]).toHaveAttribute('capture', 'environment')
  })

  it('en computadora no muestra la cámara', () => {
    render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    expect(screen.queryByText('Tomar foto')).not.toBeInTheDocument()
  })

  it('en pantallas táctiles invita a tomar la foto y "Tomar foto" es la acción principal', () => {
    window.matchMedia = vi.fn(() => ({ matches: true }))
    render(<ZonaFoto alSeleccionar={() => {}} ocupado={false} vistaPrevia={null} />)
    expect(screen.getByText('Toma una foto o elígela de tu galería.')).toBeInTheDocument()
    expect(screen.getByText('Tomar foto').closest('label')).toHaveClass('boton--principal')
    expect(screen.getByText('Elegir foto').closest('label')).toHaveClass('boton--secundario')
  })
})
