export default function Consejos({ abierto }) {
  return (
    <details className="consejos" open={abierto}>
      <summary>Consejos para una buena foto</summary>
      <ul>
        <li>Luz pareja, sin sombras duras: mejor a la sombra o con el cielo nublado.</li>
        <li>El insecto centrado y ocupando buena parte de la foto.</li>
        <li>Un fondo simple, que no se confunda con el insecto.</li>
        <li>
          JPG, PNG o WEBP de hasta 20 MB. Las fotos HEIC del iPhone no sirven: envíala como JPG
          o elige “Más compatible” en los ajustes de la cámara.
        </li>
      </ul>
    </details>
  )
}
