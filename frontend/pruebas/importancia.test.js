import { describe, expect, it } from 'vitest'
import { clasificarImportancia } from '../src/compartido/importancia.js'

describe('clasificarImportancia', () => {
  it('reconoce la plaga escrita a mano en la base', () => {
    expect(clasificarImportancia('Plaga')).toBe('plaga')
    expect(clasificarImportancia(' plaga secundaria ')).toBe('plaga')
  })

  it('reconoce lo benéfico con o sin tilde', () => {
    expect(clasificarImportancia('Benéfico - polinizador')).toBe('benefico')
    expect(clasificarImportancia('BENEFICO - depredador')).toBe('benefico')
  })

  it('no deduce nada que la ficha no diga', () => {
    expect(clasificarImportancia('')).toBeNull()
    expect(clasificarImportancia(undefined)).toBeNull()
    expect(clasificarImportancia('Sin importancia conocida')).toBeNull()
  })
})
