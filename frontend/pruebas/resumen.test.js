import { describe, expect, it } from 'vitest'
import { resumirRegistros, separarCultivos, urlRegistros } from '../src/compartido/resumen.js'

const R = (extra) => ({ ID: String(Math.random()), Importancia_economica: 'Plaga', ...extra })

describe('separarCultivos', () => {
  it('separa listas, normaliza nombres y deja fuera lo que no es cultivo', () => {
    expect(separarCultivos('Pastos; canela; árboles frutales')).toEqual(['Pastos', 'Canela', 'Frutales'])
    expect(separarCultivos('maiz, arroz y caña de azucar')).toEqual(['Maíz', 'Arroz', 'Caña de azúcar'])
    expect(separarCultivos('Ninguno (planta silvestre)')).toEqual([])
    expect(separarCultivos('Hierbas; malezas del monte')).toEqual([])
    expect(separarCultivos(null)).toEqual([])
  })
})

describe('resumirRegistros', () => {
  const registros = [
    R({ Nombre_comun: 'Gorgojo', Cultivo_asociado: 'Plátano', Tipo_de_dano: 'Barrenador', Estado_biologico: 'Adulto', Nombre_cientifico: 'Cosmopolites sordidus', Localidad: 'Zungarococha, San Juan Bautista, Loreto' }),
    R({ Nombre_comun: 'gorgojo', Cultivo_asociado: 'Plátano; yuca', Tipo_de_dano: 'Barrenador', Estado_biologico: 'Larva', Nombre_cientifico: 'No determinado', Localidad: 'Zungarococha, San Juan Bautista, Loreto' }),
    R({ Nombre_comun: 'Picudo', Cultivo_asociado: 'Camu camu', Importancia_economica: 'Plaga ocasional / potencial', Tipo_de_dano: 'No determinado', Estado_biologico: 'Adulto', Nombre_cientifico: 'Conotrachelus dubiae', Localidad: 'Iquitos, Maynas, Loreto' }),
  ]
  const r = resumirRegistros(registros)

  it('cuenta los registros', () => {
    expect(r.n).toBe(3)
  })

  it('ordena por frecuencia y une mayúsculas distintas del mismo valor', () => {
    expect(r.nombres).toEqual(['Gorgojo', 'Picudo'])
    expect(r.cultivos).toEqual([{ texto: 'Plátano', n: 2 }, { texto: 'Yuca', n: 1 }, { texto: 'Camu camu', n: 1 }])
  })

  it('cuenta la importancia registrada', () => {
    expect(r.importancias).toEqual([{ texto: 'Plaga', n: 2 }, { texto: 'Plaga ocasional / potencial', n: 1 }])
  })

  it('omite los valores no determinados', () => {
    expect(r.danos).toEqual(['Barrenador'])
    expect(r.taxones).toEqual(['Conotrachelus dubiae', 'Cosmopolites sordidus'])
  })

  it('lista estados y lugares sin repetir', () => {
    expect(r.estados).toEqual(['Adulto', 'Larva'])
    expect(r.lugares).toEqual(['Zungarococha', 'Iquitos'])
  })

  it('sin registros devuelve n = 0', () => {
    expect(resumirRegistros([]).n).toBe(0)
    expect(resumirRegistros(undefined).n).toBe(0)
  })
})

describe('urlRegistros', () => {
  it('arma la dirección de la página de registros', () => {
    expect(urlRegistros('Coleoptera', 'Curculionidae')).toBe('/registros/?orden=Coleoptera&familia=Curculionidae')
    expect(urlRegistros('Mantodea', '')).toBe('/registros/?orden=Mantodea')
  })
})
