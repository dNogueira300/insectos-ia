import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import BarraConfianza, { porcentaje } from '../src/compartido/BarraConfianza.jsx'

describe('BarraConfianza', () => {
  it('siempre escribe el porcentaje', () => {
    render(<BarraConfianza titulo="Seguridad en el orden" valor={0.914} />)
    expect(screen.getByText('91 %')).toBeInTheDocument()
    expect(screen.getByText('Seguridad en el orden')).toBeInTheDocument()
  })

  it('una familia afirmada lo dice con texto, no solo con color', () => {
    render(<BarraConfianza titulo="Familia" valor={0.98} estado="afirmada" />)
    expect(screen.getByText('Afirmada')).toBeInTheDocument()
  })

  it('una familia incierta pide revisar con un especialista', () => {
    render(<BarraConfianza titulo="Familia" valor={0.53} estado="incierta" />)
    expect(screen.getByText('Revisar con especialista')).toBeInTheDocument()
  })

  it('las candidatas no repiten la etiqueta', () => {
    render(<BarraConfianza titulo="Gomphidae" valor={0.53} estado="candidata" />)
    expect(screen.queryByText('Revisar con especialista')).not.toBeInTheDocument()
  })

  it('redondea el porcentaje', () => {
    expect(porcentaje(0.9555)).toBe('96 %')
  })
})
