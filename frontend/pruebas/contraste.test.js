// @vitest-environment node
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const css = readFileSync(new URL('../src/compartido/base.css', import.meta.url), 'utf8')

function token(nombre) {
  if (nombre.startsWith('#')) return nombre
  const hallado = css.match(new RegExp(`--${nombre}:\\s*(#[0-9a-fA-F]{6})`))
  if (!hallado) throw new Error(`falta el token --${nombre}`)
  return hallado[1]
}

function luminancia(hex) {
  const canales = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  const [r, g, b] = canales.map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contraste(a, b) {
  const [claro, oscuro] = [luminancia(a), luminancia(b)].sort((x, y) => y - x)
  return (claro + 0.05) / (oscuro + 0.05)
}

// [texto, fondo]: todos deben llegar a 4.5:1 (WCAG AA, texto normal).
const PARES = [
  ['gris', 'fondo'],
  ['gris', 'superficie'],
  ['texto-suave', 'fondo'],
  ['texto-suave', 'superficie'],
  ['petroleo', 'fondo'],
  ['verde-amazonico', 'fondo'],
  ['verde-amazonico', 'superficie'],
  ['verde-amazonico', 'selva-fondo'],
  ['ambar-texto', 'ambar-fondo'],
  ['ambar-texto', 'superficie'],
  ['gris', 'amarillo'],
  ['gris', 'ambar-fondo'],
  ['#ffffff', 'verde-amazonico'],
  ['#ffffff', 'petroleo'],
  ['texto-sobre-petroleo', 'petroleo'],
  ['verde-lima', 'petroleo'],
  ['petroleo', 'verde-lima'],
  ['error-texto', 'error-fondo'],
]

describe('contraste de los tokens de color', () => {
  it.each(PARES)('%s sobre %s llega a 4.5:1', (texto, fondo) => {
    expect(contraste(token(texto), token(fondo))).toBeGreaterThanOrEqual(4.5)
  })

  it('el enlace del crédito en la franja petróleo usa Verde Lima, no el color de enlace', () => {
    const inicio = readFileSync(new URL('../src/paginas/inicio/inicio.css', import.meta.url), 'utf8')
    expect(inicio).toMatch(/\.portada \.credito a\s*\{[^}]*color:\s*var\(--verde-lima\)/)
  })
})
