import { porcentaje } from '../../compartido/BarraConfianza.jsx'

export default function TarjetaClase({ clase, alAbrir }) {
  const { id, tipo, nombre, nombre_comun, orden, provisional, f1, foto } = clase
  return (
    <article id={id} className="tarjeta">
      <img
        className="tarjeta__foto"
        src={foto.archivo}
        alt={`Ejemplo de ${nombre}`}
        width={foto.ancho}
        height={foto.alto}
        loading="lazy"
        decoding="async"
      />
      <div className="tarjeta__cuerpo">
        <p className="tarjeta__orden">{tipo === 'familia' ? `Orden ${orden}` : 'Orden'}</p>
        <h4 className="tarjeta__nombre cientifico">{nombre}</h4>
        {nombre_comun && <p className="tarjeta__comun">{nombre_comun}</p>}
        {provisional && <span className="chip chip--provisional">Provisional</span>}
        {tipo === 'orden' && <p className="tarjeta__nota">Se identifica solo hasta orden.</p>}
        {f1 != null && (
          <div className="tarjeta__f1">
            <span>Qué tan bien la distingue (F1)</span>
            <strong>{porcentaje(f1)}</strong>
            <div className="barra__pista" aria-hidden="true">
              <div className="barra__relleno" style={{ '--valor': f1 }} />
            </div>
          </div>
        )}
        <p className="credito">
          Foto: {foto.credito} · {foto.licencia.toUpperCase()}
        </p>
        <button type="button" className="boton boton--secundario boton--chico" onClick={alAbrir}>
          Ver fichas
        </button>
      </div>
    </article>
  )
}
