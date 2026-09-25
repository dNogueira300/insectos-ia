// La base escribe la importancia a mano ("Plaga", "Benéfico - polinizador"). Se
// normaliza solo para elegir el estilo del chip: el texto que se muestra es el
// de la ficha, y si no se reconoce no se deduce nada.
export function clasificarImportancia(texto) {
  const limpio = (texto ?? '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
  if (limpio.startsWith('plaga')) return 'plaga'
  if (limpio.startsWith('benefico')) return 'benefico'
  return null
}
