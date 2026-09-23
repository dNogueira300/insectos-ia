// Campos visibles y su etiqueta, en el orden que le sirve a agronomía.
const CAMPOS = [
  ['Nombre_comun', 'Nombre común'],
  ['Nombre_cientifico', 'Nombre científico'],
  ['Cultivo_asociado', 'Cultivo asociado'],
  ['Tipo_de_dano', 'Tipo de daño'],
  ['Importancia_economica', 'Importancia económica'],
  ['Hospedero', 'Hospedero'],
  ['Localidad', 'Localidad'],
  ['Estado_biologico', 'Estado biológico'],
  ['Verificado_por', 'Verificado por'],
]

export default function Ficha({ fichas }) {
  if (!fichas || fichas.length === 0) {
    return (
      <section className="ficha">
        <p className="ayuda">
          No hay registros en la base de datos biológica para este taxón todavía.
        </p>
      </section>
    )
  }

  return (
    <section className="ficha">
      <h2>Información biológica</h2>
      {fichas.map((registro) => (
        <table
          key={registro.ID}
          className={registro.Importancia_economica === 'plaga' ? 'plaga' : undefined}
        >
          <tbody>
            {CAMPOS.filter(([clave]) => registro[clave]).map(([clave, etiqueta]) => (
              <tr key={clave}>
                <th scope="row">{etiqueta}</th>
                <td>{registro[clave]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
    </section>
  )
}
