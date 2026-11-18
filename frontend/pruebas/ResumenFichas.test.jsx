import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ResumenFichas from '../src/compartido/ResumenFichas.jsx'

const FICHAS = [
  { ID: '1', Nombre_comun: 'Gorgojo', Cultivo_asociado: 'Plátano', Importancia_economica: 'Plaga', Tipo_de_dano: 'Barrenador', Estado_biologico: 'Adulto', Nombre_cientifico: 'Cosmopolites sordidus', Localidad: 'Zungarococha, San Juan Bautista, Loreto', Verificado_por: 'Una Persona' },
  { ID: '2', Nombre_comun: 'Gorgojo', Cultivo_asociado: 'Yuca', Importancia_economica: 'Plaga', Tipo_de_dano: 'Barrenador', Estado_biologico: 'Larva', Nombre_cientifico: 'No determinado', Localidad: 'Zungarococha' },
]

describe('ResumenFichas', () => {
  it('resume los registros en una sola ficha con su título', () => {
    render(<ResumenFichas fichas={FICHAS} orden="Coleoptera" familia="Curculionidae" titulo="Registros de la base para la familia Curculionidae" />)
    expect(screen.getByRole('heading', { name: 'Registros de la base para la familia Curculionidae' })).toBeInTheDocument()
    expect(screen.getByText(/Resumen de 2 registros/)).toBeInTheDocument()
    expect(screen.getAllByRole('article')).toHaveLength(1)
  })

  it('explica de dónde salen los datos y que no son la identificación de la foto', () => {
    render(<ResumenFichas fichas={FICHAS} orden="Coleoptera" familia="Curculionidae" />)
    expect(screen.getByText(/fotografiados por estudiantes/)).toBeInTheDocument()
    expect(screen.getByText(/no la especie de tu foto/)).toBeInTheDocument()
  })

  it('resalta los cultivos y la importancia', () => {
    const { container } = render(<ResumenFichas fichas={FICHAS} orden="Coleoptera" familia="Curculionidae" />)
    expect([...container.querySelectorAll('.chip--cultivo')].map((c) => c.textContent)).toEqual(['Plátano', 'Yuca'])
    expect(container.querySelector('.chip--plaga')).toHaveTextContent('Plaga · 2')
  })

  it('muestra los datos de la familia sin nombres de personas', () => {
    render(<ResumenFichas fichas={FICHAS} orden="Coleoptera" familia="Curculionidae" />)
    expect(screen.getByText('Cosmopolites sordidus')).toBeInTheDocument()
    expect(screen.getByText('Barrenador')).toBeInTheDocument()
    expect(screen.getByText('Adulto, Larva')).toBeInTheDocument()
    expect(screen.queryByText('Una Persona')).not.toBeInTheDocument()
  })

  it('enlaza a la página con todos los registros', () => {
    render(<ResumenFichas fichas={FICHAS} orden="Coleoptera" familia="Curculionidae" />)
    expect(screen.getByRole('link', { name: 'Ver los 2 registros' })).toHaveAttribute('href', '/registros/?orden=Coleoptera&familia=Curculionidae')
  })

  it('puede omitir el enlace (en la propia página de registros)', () => {
    render(<ResumenFichas fichas={FICHAS} orden="Coleoptera" familia="Curculionidae" enlace={false} />)
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('sin registros muestra el aviso que se le pase', () => {
    render(<ResumenFichas fichas={[]} orden="Mantodea" vacio="Aún no hay fichas de este orden en la base." />)
    expect(screen.getByText('Aún no hay fichas de este orden en la base.')).toBeInTheDocument()
  })
})
