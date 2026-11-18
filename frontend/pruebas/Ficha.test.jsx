import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Ficha from '../src/compartido/Ficha.jsx'

const REGISTRO = {
  ID: 'INS-0001',
  Nombre_comun: 'gorgojo del plátano',
  Nombre_cientifico: 'Cosmopolites sordidus',
  Cultivo_asociado: 'plátano',
  Tipo_de_dano: 'perforación del cormo',
  Importancia_economica: 'Plaga',
  Hospedero: 'Musa spp.',
  Localidad: 'Iquitos',
  Estado_biologico: 'adulto',
  Verificado_por: '(pendiente)',
  Archivo_imagen: 'x.jpg',
  Observaciones: 'nota interna',
}

describe('Ficha', () => {
  it('avisa cuando no hay registros, con el texto que se le pase', () => {
    render(<Ficha fichas={[]} vacio="Aún no hay fichas de esta familia en la base." />)
    expect(screen.getByText('Aún no hay fichas de esta familia en la base.')).toBeInTheDocument()
  })

  it('avisa igual si no le pasan nada', () => {
    render(<Ficha />)
    expect(screen.getByText(/no hay registros/i)).toBeInTheDocument()
  })

  it('muestra los datos que le sirven a agronomía', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.getByText('gorgojo del plátano')).toBeInTheDocument()
    expect(screen.getByText('Cosmopolites sordidus')).toBeInTheDocument()
    expect(screen.getByText('perforación del cormo')).toBeInTheDocument()
  })

  it('no muestra campos de control interno', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.queryByText('nota interna')).not.toBeInTheDocument()
    expect(screen.queryByText('x.jpg')).not.toBeInTheDocument()
  })

  it('omite los campos vacíos', () => {
    render(<Ficha fichas={[{ ...REGISTRO, Localidad: '' }]} />)
    expect(screen.queryByText('Localidad')).not.toBeInTheDocument()
  })

  it('marca como plaga lo que la base escribe "Plaga", con mayúscula', () => {
    const { container } = render(<Ficha fichas={[REGISTRO]} />)
    expect(container.querySelector('.chip--plaga')).toHaveTextContent('Plaga')
  })

  it('marca lo benéfico con su detalle', () => {
    render(<Ficha fichas={[{ ...REGISTRO, Importancia_economica: 'Benéfico - polinizador' }]} />)
    expect(screen.getByText('Benéfico - polinizador')).toHaveClass('chip--benefico')
  })

  it('una importancia no reconocida se muestra como dato, sin chip', () => {
    const { container } = render(<Ficha fichas={[{ ...REGISTRO, Importancia_economica: 'Variable' }]} />)
    expect(container.querySelector('.chip--plaga, .chip--benefico')).toBeNull()
    expect(screen.getByText('Variable')).toBeInTheDocument()
  })

  it('acepta un título que aclara de qué taxón son los registros', () => {
    render(<Ficha fichas={[REGISTRO]} titulo="Registros del orden Coleoptera en la base" />)
    expect(screen.getByRole('heading', { name: 'Registros del orden Coleoptera en la base' })).toBeInTheDocument()
  })

  it('rotula el nombre científico como la especie del registro, no como la identificación', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.getByText('Especie del registro')).toBeInTheDocument()
    expect(screen.queryByText('Nombre científico')).not.toBeInTheDocument()
  })

  it('no muestra quién verificó la ficha: la interfaz no lleva nombres de personas', () => {
    render(<Ficha fichas={[{ ...REGISTRO, Verificado_por: 'Una Persona' }]} />)
    expect(screen.queryByText('Una Persona')).not.toBeInTheDocument()
    expect(screen.queryByText('Verificado por')).not.toBeInTheDocument()
  })

  it('resalta el cultivo asociado como chip, igual que la importancia', () => {
    const { container } = render(<Ficha fichas={[REGISTRO]} />)
    expect(container.querySelector('.chip--cultivo')).toHaveTextContent('Cultivo: plátano')
    expect(screen.queryByText('Cultivo asociado')).not.toBeInTheDocument()
  })

  it('una planta silvestre no se resalta como cultivo', () => {
    const { container } = render(<Ficha fichas={[{ ...REGISTRO, Cultivo_asociado: 'Ninguno (planta silvestre)' }]} />)
    expect(container.querySelector('.chip--cultivo')).toBeNull()
    expect(screen.getByText('Ninguno (planta silvestre)')).toBeInTheDocument()
  })

  it('no muestra la especie cuando no está determinada', () => {
    render(<Ficha fichas={[{ ...REGISTRO, Nombre_cientifico: 'No determinado' }]} />)
    expect(screen.queryByText('Especie del registro')).not.toBeInTheDocument()
  })

  it('pone primero las fichas con especie o género determinados', () => {
    const fichas = [
      { ...REGISTRO, ID: 'A', Nombre_comun: 'sin especie', Nombre_cientifico: 'No determinado' },
      { ...REGISTRO, ID: 'B', Nombre_comun: 'con género', Nombre_cientifico: 'Atta sp.' },
    ]
    render(<Ficha fichas={fichas} />)
    const nombres = screen.getAllByText(/sin especie|con género/).map((n) => n.textContent)
    expect(nombres).toEqual(['con género', 'sin especie'])
  })

  it('muestra seis fichas y un botón para ver las demás', async () => {
    const fichas = Array.from({ length: 9 }, (_, i) => ({ ...REGISTRO, ID: `R${i}`, Nombre_comun: `insecto ${i}` }))
    render(<Ficha fichas={fichas} />)
    expect(screen.getAllByText(/^insecto \d$/)).toHaveLength(6)
    fireEvent.click(screen.getByRole('button', { name: 'Ver 3 fichas más' }))
    expect(screen.getAllByText(/^insecto \d$/)).toHaveLength(9)
  })
})
