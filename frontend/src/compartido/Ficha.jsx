import { useState } from 'react'
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

// Fichas que se ven antes de pedir el resto: una familia común puede tener decenas.
const VISIBLES = 6

const sinDeterminar = (texto) => /^no determinad/i.test((texto ?? '').trim())

// "Ninguno (planta silvestre)" es un dato, no un cultivo: no se resalta.
const esCultivo = (texto) => Boolean(texto) && !/^ninguno/i.test(texto.trim())

export default function Ficha({
  fichas,
  titulo = 'Información biológica',
  nota,
  vacio = 'No hay registros en la base de datos biológica para este taxón todavía.',
  visibles = VISIBLES,
}) {
  const [todas, setTodas] = useState(false)

  if (!fichas || fichas.length === 0) {
    return (
      <section className="ficha">
        <p className="ayuda">{vacio}</p>
      </section>
    )
  }

  // Primero las fichas con especie o género conocidos: describen mejor al grupo.
  const ordenadas = [...fichas].sort(
    (a, b) => sinDeterminar(a.Nombre_cientifico) - sinDeterminar(b.Nombre_cientifico),
  )
  const mostradas = todas ? ordenadas : ordenadas.slice(0, visibles)
  const restantes = ordenadas.length - mostradas.length

  return (
    <section className="ficha">
      <h2 className="ficha__titulo">{titulo}</h2>
      {nota && <p className="ayuda">{nota}</p>}
      {mostradas.map((registro) => {
        const tipo = clasificarImportancia(registro.Importancia_economica)
        const cultivo = esCultivo(registro.Cultivo_asociado)
        // Lo que ya se lee en un chip no se repite en la lista.
        const campos = CAMPOS.filter(
          ([clave]) =>
            registro[clave] &&
            !(tipo && clave === 'Importancia_economica') &&
            !(cultivo && clave === 'Cultivo_asociado') &&
            // 'No determinado' no le dice nada al lector: el campo se omite.
            !sinDeterminar(registro[clave]),
        )
        return (
          <article key={registro.ID} className="ficha__registro">
            {(tipo || cultivo) && (
              <div className="ficha__chips">
                {tipo && <span className={`chip chip--${tipo}`}>{registro.Importancia_economica}</span>}
                {cultivo && (
                  <span className="chip chip--cultivo">Cultivo: {registro.Cultivo_asociado}</span>
                )}
              </div>
            )}
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
      {restantes > 0 && (
        <button type="button" className="boton boton--secundario boton--chico" onClick={() => setTodas(true)}>
          {`Ver ${restantes} ${restantes === 1 ? 'ficha' : 'fichas'} más`}
        </button>
      )}
    </section>
  )
}
