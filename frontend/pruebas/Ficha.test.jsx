import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Ficha from '../src/componentes/Ficha.jsx'

const REGISTRO = {
  ID: 'INS-0001',
  Nombre_comun: 'gorgojo del plátano',
  Nombre_cientifico: 'Cosmopolites sordidus',
  Cultivo_asociado: 'plátano',
  Tipo_de_dano: 'perforación del cormo',
  Importancia_economica: 'plaga',
  Hospedero: 'Musa spp.',
  Localidad: 'Iquitos',
  Estado_biologico: 'adulto',
  Verificado_por: 'M. Ruiz',
  Archivo_imagen: 'x.jpg',
  Observaciones: 'nota interna',
}

describe('Ficha', () => {
  it('avisa cuando no hay registros', () => {
    render(<Ficha fichas={[]} />)
    expect(screen.getByText(/no hay registros/i)).toBeInTheDocument()
  })

  it('avisa igual si no le pasan nada', () => {
    render(<Ficha />)
    expect(screen.getByText(/no hay registros/i)).toBeInTheDocument()
  })

  it('muestra el nombre común y el científico', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.getByText('gorgojo del plátano')).toBeInTheDocument()
    expect(screen.getByText('Cosmopolites sordidus')).toBeInTheDocument()
  })

  it('muestra el cultivo asociado y el tipo de daño', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.getByText('plátano')).toBeInTheDocument()
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

  it('muestra varios registros', () => {
    render(<Ficha fichas={[REGISTRO, { ...REGISTRO, ID: 'INS-0002', Nombre_comun: 'otro' }]} />)
    expect(screen.getByText('gorgojo del plátano')).toBeInTheDocument()
    expect(screen.getByText('otro')).toBeInTheDocument()
  })

  it('destaca los registros marcados como plaga', () => {
    const { container } = render(<Ficha fichas={[REGISTRO]} />)
    expect(container.querySelector('.plaga')).not.toBeNull()
  })
})
