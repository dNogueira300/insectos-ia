import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Resultado from '../src/compartido/Resultado.jsx'

const CERTERO = {
  orden: 'Coleoptera',
  confianza_orden: 0.94,
  familia: 'Curculionidae',
  confianza_familia: 0.81,
  familia_incierta: false,
  top_familias: [
    { familia: 'Curculionidae', confianza: 0.81 },
    { familia: 'Chrysomelidae', confianza: 0.12 },
  ],
  fichas: [],
}
const INCIERTO = { ...CERTERO, confianza_familia: 0.31, familia_incierta: true }
const SIN_FAMILIAS = { ...CERTERO, orden: 'Mantodea', familia: '', familia_incierta: true, top_familias: [] }

describe('Resultado', () => {
  it('no muestra nada sin predicción', () => {
    const { container } = render(<Resultado prediccion={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('muestra la ruta orden → familia y ambas confianzas', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByText('Coleoptera')).toBeInTheDocument()
    expect(screen.getByText('Curculionidae')).toBeInTheDocument()
    expect(screen.getByText('94 %')).toBeInTheDocument()
    expect(screen.getByText('81 %')).toBeInTheDocument()
    expect(screen.getByText('Afirmada')).toBeInTheDocument()
  })

  it('enlaza la familia afirmada con su tarjeta del catálogo', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByRole('link', { name: 'Ver esta familia en el catálogo' })).toHaveAttribute('href', '/#familia-Curculionidae')
  })

  it('con familia incierta no la afirma y muestra las candidatas', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText(/no se puede determinar la familia/i)).toBeInTheDocument()
    expect(screen.getByText('Chrysomelidae')).toBeInTheDocument()
    expect(screen.queryByText('Afirmada')).not.toBeInTheDocument()
  })

  it('con familia incierta sigue mostrando el orden y enlaza al orden', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText('Coleoptera')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ver este orden en el catálogo' })).toHaveAttribute('href', '/#orden-Coleoptera')
  })

  it('un orden sin familias no se presenta como duda', () => {
    render(<Resultado prediccion={SIN_FAMILIAS} />)
    expect(screen.getByText(/no se clasifica por familia/i)).toBeInTheDocument()
    expect(screen.queryByText(/no se puede determinar/i)).not.toBeInTheDocument()
  })

  it('muestra el chip de plaga solo si la ficha lo dice y la familia está afirmada', () => {
    const conFicha = { ...CERTERO, fichas: [{ ID: '1', Importancia_economica: 'Plaga' }] }
    const { rerender, container } = render(<Resultado prediccion={conFicha} />)
    expect(container.querySelector('.chip--plaga')).not.toBeNull()
    rerender(<Resultado prediccion={{ ...conFicha, familia_incierta: true }} />)
    expect(container.querySelector('.chip--plaga')).toBeNull()
  })

  it('en la portada va sin enlace', () => {
    render(<Resultado prediccion={CERTERO} conEnlace={false} />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
