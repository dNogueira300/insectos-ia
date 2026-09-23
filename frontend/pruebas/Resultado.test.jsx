import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Resultado from '../src/componentes/Resultado.jsx'

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

describe('Resultado', () => {
  it('no muestra nada sin predicción', () => {
    const { container } = render(<Resultado prediccion={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('muestra el orden y su confianza en porcentaje', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByText(/Coleoptera/)).toBeInTheDocument()
    expect(screen.getByText(/94\s*%/)).toBeInTheDocument()
  })

  it('muestra la familia cuando hay certeza', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByText('Curculionidae')).toBeInTheDocument()
    expect(screen.getByText(/81\s*%/)).toBeInTheDocument()
  })

  it('avisa cuando la familia es incierta', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText(/incierta|no se puede determinar/i)).toBeInTheDocument()
  })

  it('con familia incierta muestra las candidatas', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText('Chrysomelidae')).toBeInTheDocument()
  })

  it('el orden se sigue mostrando aunque la familia sea incierta', () => {
    render(<Resultado prediccion={INCIERTO} />)
    // Texto exacto: el orden también aparece dentro de la frase de candidatas.
    expect(screen.getByText('Coleoptera')).toBeInTheDocument()
  })

  it('maneja un orden sin familias entrenadas', () => {
    render(
      <Resultado
        prediccion={{ ...CERTERO, familia: '', familia_incierta: true, top_familias: [] }}
      />,
    )
    expect(screen.getByText(/Coleoptera/)).toBeInTheDocument()
    expect(screen.queryByText('Curculionidae')).not.toBeInTheDocument()
  })

  it('un orden sin familias en el sistema no se presenta como duda', () => {
    // Seis órdenes (Mantodea, Phasmida, …) no se clasifican por familia: decir
    // "no se puede determinar" sugeriría que el modelo dudó.
    render(
      <Resultado
        prediccion={{ ...CERTERO, familia: '', familia_incierta: true, top_familias: [] }}
      />,
    )
    expect(screen.getByText(/no se clasifica por familia/i)).toBeInTheDocument()
    expect(screen.queryByText(/no se puede determinar/i)).not.toBeInTheDocument()
  })

  it('marca visualmente el estado incierto', () => {
    const { container } = render(<Resultado prediccion={INCIERTO} />)
    expect(container.querySelector('.incierto')).not.toBeNull()
  })
})
