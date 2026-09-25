// "cc-by-nc" -> "CC BY-NC": la licencia como se escribe en español y en la
// propia Creative Commons.
export function textoLicencia(licencia) {
  if (!licencia) return 'licencia no registrada'
  if (licencia.toLowerCase() === 'cc0') return 'CC0'
  return licencia.toUpperCase().replace(/^CC-/, 'CC ')
}

// Crédito de una foto de iNaturalist: el autor, enlazado a su observación
// cuando se conoce, y la licencia.
export default function Credito({ foto }) {
  const autor = foto.url_origen ? (
    <a href={foto.url_origen} target="_blank" rel="noreferrer">
      {foto.credito}
    </a>
  ) : (
    foto.credito
  )
  return (
    <p className="credito">
      Foto: {autor} · {textoLicencia(foto.licencia)}
    </p>
  )
}
