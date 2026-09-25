import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Credito, { textoLicencia } from '../src/compartido/Credito.jsx'

describe('Credito', () => {
  it('escribe la licencia como se lee', () => {
    expect(textoLicencia('cc-by-nc-sa')).toBe('CC BY-NC-SA')
    expect(textoLicencia('cc0')).toBe('CC0')
    expect(textoLicencia('')).toBe('licencia no registrada')
  })

  it('enlaza el autor a la observación de origen', () => {
    render(<Credito foto={{ credito: 'Zack Abbey', licencia: 'cc-by', url_origen: 'https://www.inaturalist.org/observations/1' }} />)
    expect(screen.getByText(/Zack Abbey/).closest('p')).toHaveTextContent('Foto: Zack Abbey · CC BY')
    expect(screen.getByRole('link', { name: 'Zack Abbey' })).toHaveAttribute('href', 'https://www.inaturalist.org/observations/1')
  })

  it('sin enlace de origen, el autor va como texto', () => {
    render(<Credito foto={{ credito: 'Autor no registrado', licencia: 'cc-by', url_origen: '' }} />)
    expect(screen.queryByRole('link')).toBeNull()
    expect(screen.getByText(/Autor no registrado/)).toBeInTheDocument()
  })
})
