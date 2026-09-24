import { fireEvent, render } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import SubirFoto from '../src/componentes/SubirFoto.jsx'

const foto = () => new File(['x'], 'insecto.jpg', { type: 'image/jpeg' })
const entrada = (container) => container.querySelector('input[type="file"]')

describe('SubirFoto', () => {
  let numero
  beforeEach(() => {
    numero = 0
    URL.createObjectURL = vi.fn(() => `blob:${++numero}`)
    URL.revokeObjectURL = vi.fn()
  })
  afterEach(() => vi.restoreAllMocks())

  it('entrega el archivo elegido', () => {
    const alSeleccionar = vi.fn()
    const { container } = render(<SubirFoto alSeleccionar={alSeleccionar} ocupado={false} />)
    const archivo = foto()
    fireEvent.change(entrada(container), { target: { files: [archivo] } })
    expect(alSeleccionar).toHaveBeenCalledWith(archivo)
  })

  it('deja listo un selector nuevo para poder elegir otra vez la misma foto', () => {
    // El navegador no avisa un cambio si se elige el mismo archivo en el mismo
    // selector: por ejemplo, para reintentar después de un error de conexión.
    const { container } = render(<SubirFoto alSeleccionar={vi.fn()} ocupado={false} />)
    const antes = entrada(container)
    fireEvent.change(antes, { target: { files: [foto()] } })
    expect(entrada(container)).not.toBe(antes)
  })

  it('libera la vista previa anterior al elegir otra foto', () => {
    const { container } = render(<SubirFoto alSeleccionar={vi.fn()} ocupado={false} />)
    fireEvent.change(entrada(container), { target: { files: [foto()] } })
    fireEvent.change(entrada(container), { target: { files: [foto()] } })
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:1')
  })

  it('libera la vista previa al desmontarse', () => {
    const { container, unmount } = render(<SubirFoto alSeleccionar={vi.fn()} ocupado={false} />)
    fireEvent.change(entrada(container), { target: { files: [foto()] } })
    unmount()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:1')
  })
})
