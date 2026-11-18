// Resumen de los registros de la base de una familia (u orden): lo que se muestra
// en una sola ficha en vez de decenas de tarjetas. Todo sale de los registros;
// no se deduce nada que la base no diga.

const clave = (texto) =>
  (texto ?? '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')

const sinDato = (texto) => {
  const k = clave(texto)
  return !k || k.startsWith('no determinad') || k === 'no aplica'
}

const mayuscula = (texto) => texto.charAt(0).toUpperCase() + texto.slice(1)

// Lo que los alumnos escribieron como "cultivo" pero no lo es.
const NO_CULTIVO = ['hierba', 'maleza', 'herbacea', 'helecho', 'vegetacion', 'maderable', 'forestal', 'silvestre',
  'arbustiv', 'arbusto', 'medicinal', 'ninguno', 'no determinad', 'varios', 'plantas', 'monte', 'follaje']
const NOMBRE_CULTIVO = {
  maiz: 'Maíz', maices: 'Maíz', platano: 'Plátano', platanal: 'Plátano', 'arboles frutales': 'Frutales',
  frutales: 'Frutales', citricos: 'Cítricos', 'cana de azucar': 'Caña de azúcar', cana: 'Caña de azúcar',
  'camu camu': 'Camu camu', 'camu-camu': 'Camu camu', caupi: 'Caupí', 'frijol caupi': 'Caupí', pasto: 'Pastos',
  pastos: 'Pastos', gramineas: 'Pastos', pinones: 'Piñón', pina: 'Piña', cafe: 'Café', limon: 'Limón',
  maracuya: 'Maracuyá', guanabana: 'Guanábana',
}

export function separarCultivos(texto) {
  if (!texto) return []
  const vistos = new Set()
  const salida = []
  for (const parte of texto.split(/\s*[;,/]\s*|\s+y\s+/)) {
    const limpio = parte.trim().replace(/\.$/, '')
    const k = clave(limpio)
    if (!k || NO_CULTIVO.some((n) => k.includes(n))) continue
    const nombre = NOMBRE_CULTIVO[k] ?? mayuscula(limpio.toLowerCase())
    if (!vistos.has(nombre)) {
      vistos.add(nombre)
      salida.push(nombre)
    }
  }
  return salida
}

// Cuenta valores agrupando mayúsculas y tildes distintas; conserva la primera
// forma escrita y el orden de aparición para los empates.
function contar(valores) {
  const mapa = new Map()
  valores.forEach((valor) => {
    if (sinDato(valor)) return
    const k = clave(valor)
    const actual = mapa.get(k)
    if (actual) actual.n += 1
    else mapa.set(k, { texto: mayuscula(valor.trim()), n: 1 })
  })
  return [...mapa.values()].sort((a, b) => b.n - a.n)
}

export function resumirRegistros(registros) {
  const lista = registros ?? []
  const campo = (nombre) => lista.map((r) => r[nombre])
  return {
    n: lista.length,
    nombres: contar(campo('Nombre_comun')).map((c) => c.texto),
    importancias: contar(campo('Importancia_economica')),
    cultivos: contar(lista.flatMap((r) => separarCultivos(r.Cultivo_asociado))),
    danos: contar(campo('Tipo_de_dano')).map((c) => c.texto),
    estados: contar(campo('Estado_biologico')).map((c) => c.texto),
    taxones: [...new Set(campo('Nombre_cientifico').filter((t) => !sinDato(t)).map((t) => t.trim()))].sort(),
    lugares: contar(campo('Localidad').map((l) => (l ?? '').split(',')[0])).map((c) => c.texto),
  }
}

export function urlRegistros(orden, familia = '') {
  const consulta = new URLSearchParams({ orden })
  if (familia) consulta.set('familia', familia)
  return `/registros/?${consulta.toString()}`
}
