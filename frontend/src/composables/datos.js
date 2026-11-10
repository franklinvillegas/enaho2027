// Utilidades para interpretar las filas que devuelve la API sin conocer de antemano
// sus columnas (los procedimientos actuales devuelven columnas distintas por nivel).

export const esNumero = (v) => typeof v === 'number' || (typeof v === 'string' && v.trim() !== '' && !Number.isNaN(Number(v)))

/** Separa columnas en categóricas y numéricas mirando los valores de las filas. */
export function clasificarColumnas(columnas, filas) {
  const numericas = []
  const categoricas = []
  for (const c of columnas) {
    const valores = filas.map((f) => f[c]).filter((v) => v !== null && v !== undefined && v !== '')
    if (valores.length && valores.every(esNumero)) numericas.push(c)
    else categoricas.push(c)
  }
  return { numericas, categoricas }
}

/** Medida a graficar por defecto: una tasa o porcentaje si existe; si no, la primera numérica. */
export function medidaPrincipal(numericas) {
  return numericas.find((c) => /tasa|porc|pct|%/i.test(c)) ?? numericas[0] ?? null
}

const LAT =/^(lat|latitud|latitude|gps_lat|y)$/i
const LON = /^(lon|lng|long|longitud|longitude|gps_lon|x)$/i

/** Busca columnas de coordenadas para el mapa. */
export function columnasCoordenadas(columnas) {
  return { lat: columnas.find((c) => LAT.test(c)), lon: columnas.find((c) => LON.test(c)) }
}

/** Convierte "tasa_no_respuesta" o "TasaNoRespuesta" en "Tasa no respuesta". */
export function etiqueta(columna) {
  const texto = String(columna)
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .trim()
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}
