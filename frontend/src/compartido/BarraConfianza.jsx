export const porcentaje = (valor) => `${Math.round(valor * 100)} %`

const ETIQUETAS = { afirmada: 'Afirmada', incierta: 'Revisar con especialista' }

// La confianza nunca depende solo del color: el porcentaje, y en la familia la
// etiqueta, van escritos. La barra es un refuerzo visual (aria-hidden).
export default function BarraConfianza({ titulo, valor, estado = 'neutra' }) {
  const etiqueta = ETIQUETAS[estado]
  return (
    <div className={`barra barra--${estado}`}>
      <div className="barra__encabezado">
        <span className="barra__titulo">{titulo}</span>
        <span className="barra__valor">{porcentaje(valor)}</span>
      </div>
      <div className="barra__pista" aria-hidden="true">
        <div className="barra__relleno" style={{ '--valor': valor }} />
      </div>
      {etiqueta && <span className="barra__etiqueta">{etiqueta}</span>}
    </div>
  )
}
