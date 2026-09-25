import { clasificarImportancia } from './importancia.js'

// Campos visibles y su etiqueta, en el orden que le sirve a agronomía. Los de
// control interno (ID, Archivo_imagen, Fuente, Observaciones) no se muestran, ni
// Verificado_por: la interfaz no lleva nombres de personas.
const CAMPOS = [
  ['Nombre_comun', 'Nombre común'],
  // Las fichas describen especies registradas en la base; el sistema identifica
  // solo hasta familia, así que no se rotula como si fuera la identificación.
  ['Nombre_cientifico', 'Especie del registro'],
  ['Cultivo_asociado', 'Cultivo asociado'],
  ['Tipo_de_dano', 'Tipo de daño'],
  ['Importancia_economica', 'Importancia económica'],
  ['Hospedero', 'Hospedero'],
  ['Localidad', 'Localidad'],
  ['Estado_biologico', 'Estado biológico'],
]

export default function Ficha({
  fichas,
  titulo = 'Información biológica',
  nota,
  vacio = 'No hay registros en la base de datos biológica para este taxón todavía.',
}) {
  if (!fichas || fichas.length === 0) {
    return (
      <section className="ficha">
        <p className="ayuda">{vacio}</p>
      </section>
    )
  }

  return (
    <section className="ficha">
      <h2 className="ficha__titulo">{titulo}</h2>
      {nota && <p className="ayuda">{nota}</p>}
      {fichas.map((registro) => {
        const tipo = clasificarImportancia(registro.Importancia_economica)
        // Si hay chip, la importancia ya se lee ahí: no se repite en la lista.
        const campos = CAMPOS.filter(
          ([clave]) => registro[clave] && !(tipo && clave === 'Importancia_economica'),
        )
        return (
          <article key={registro.ID} className="ficha__registro">
            {tipo && <span className={`chip chip--${tipo}`}>{registro.Importancia_economica}</span>}
            <dl className="ficha__datos">
              {campos.map(([clave, etiqueta]) => (
                <div key={clave} className="ficha__dato">
                  <dt>{etiqueta}</dt>
                  <dd className={clave === 'Nombre_cientifico' ? 'cientifico' : undefined}>
                    {registro[clave]}
                  </dd>
                </div>
              ))}
            </dl>
          </article>
        )
      })}
    </section>
  )
}
