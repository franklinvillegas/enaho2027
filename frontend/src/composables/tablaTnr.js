// Arma la tabla de TNR a partir de las columnas que devuelve el procedimiento.
// En el sistema actual los años (2012–2026) y los meses (2025 y 2026) estaban escritos
// a mano en el JavaScript; aquí salen de los datos, así no hay que editar el código
// cada año.

export const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
  'setiembre', 'octubre', 'noviembre', 'diciembre']
export const MESES_CORTOS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct',
  'Nov', 'Dic']

const escapar = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const reAnio = (prefijo) => new RegExp(`^${escapar(prefijo)}(\\d{4})$`, 'i')
const RE_MES = new RegExp(`^(${MESES.join('|')})_(\\d{4})$`, 'i')

/** Años con columna <prefijo>AAAA (tnr2026, tnrp_2026), ordenados. */
export function aniosDe(columnas, prefijo = 'tnr') {
  const re = reAnio(prefijo)
  return columnas.map((c) => c.match(re)?.[1]).filter(Boolean).map(Number).sort((a, b) => a - b)
}

/** Años que tienen columnas mensuales (enero_2026, ...). */
export function aniosConMeses(columnas) {
  const anios = new Set(columnas.map((c) => c.match(RE_MES)?.[2]).filter(Boolean).map(Number))
  return [...anios].sort((a, b) => a - b)
}

/**
 * Modelo de columnas de datos para la tabla.
 * - Si hay columnas mensuales: por cada año → Total, Abs, Ene, Abs, ... Dic, Abs.
 * - Si no: una columna por año (tnrAAAA), con su "Abs." al lado si el procedimiento
 *   lo devuelve (tnrp_2026_abs en la TNR parcial).
 * prefijo: 'tnr' (TNR total) o 'tnrp_' (TNR parcial).
 * colorearUltimo: marca la última columna de tasa para la escala azul (solo TNR total).
 */
export function modeloColumnas(columnas, { prefijo = 'tnr', colorearUltimo = true } = {}) {
  const conMeses = aniosConMeses(columnas)
  if (conMeses.length) {
    const grupos = conMeses.map((anio) => {
      const cols = []
      if (columnas.includes(`${prefijo}${anio}`)) {
        cols.push({ clave: `${prefijo}${anio}`, titulo: 'Total', tasa: true })
        cols.push({ clave: `${prefijo}${anio}_abs`, titulo: 'Abs' })
      }
      MESES.forEach((m, i) => {
        const mes = String(i + 1).padStart(2, '0')
        cols.push({ clave: `${m}_${anio}`, titulo: MESES_CORTOS[i], tasa: true, mes })
        cols.push({ clave: `${m}_${anio}_abs`, titulo: 'Abs', mes })
      })
      return { anio, columnas: cols.filter((c) => columnas.includes(c.clave)) }
    })
    return { tipo: 'meses', grupos }
  }
  const anios = aniosDe(columnas, prefijo)
  const cols = anios.flatMap((a, i) => {
    const tasa = { clave: `${prefijo}${a}`, titulo: String(a), tasa: true,
      colorear: colorearUltimo && i === anios.length - 1 }
    const abs = `${prefijo}${a}_abs`
    return columnas.includes(abs) ? [tasa, { clave: abs, titulo: 'Abs.' }] : [tasa]
  })
  return { tipo: 'anios', grupos: [{ anio: null, columnas: cols }] }
}

/** Escala azul de la última columna (colorCasilla, caso 6, del sistema actual). */
export function colorCasilla(valor) {
  const v = Number(valor)
  if (v <= 33.33) return { fondo: '#DCF2FD', texto: '#000000' }
  if (v <= 66.66) return { fondo: '#ACD6F2', texto: '#FFFFFF' }
  if (v <= 89.99) return { fondo: '#4DBEED', texto: '#FFFFFF' }
  if (v <= 99.99) return { fondo: '#00A5E8', texto: '#FFFFFF' }
  return { fondo: '#007DC5', texto: '#FFFFFF' }
}

export function formatear(valor, esTasa) {
  if (valor === null || valor === undefined || valor === '') return '-'
  const n = Number(valor)
  if (Number.isNaN(n)) return String(valor)
  return esTasa ? n.toFixed(1) : String(Math.round(n))
}

/**
 * N° de la fila, tal como lo envía el procedimiento (igual que la pantalla actual):
 * en el primer nivel (nacional) es idMostrar; al bajar a sede, encuestador o
 * conglomerado es id (idMostrar ahí trae el código de la ODEI, no el número de fila).
 */
export const idFila = (fila, nivel = 1) => (nivel > 1 ? (fila.id ?? fila.idMostrar) : (fila.idMostrar ?? fila.id))

/** Fila resaltada en amarillo: la primera (total) y, en el nivel nacional, los títulos de sección. */
export const esFilaTotal = (fila, i, nivel = 1) => i === 0 || (nivel === 1 && Number(idFila(fila)) === 0)

/**
 * Valores mensuales de un año para el gráfico de líneas. En el año en curso se cortan
 * los meses que aún no llegan (igual que la pantalla actual), para que la línea no caiga a 0.
 */
export function serieMensual(fila, anio, hoy = new Date()) {
  const valores = MESES.map((m) => fila[`${m}_${anio}`] ?? null)
  return anio === hoy.getFullYear() ? valores.slice(0, hoy.getMonth() + 1) : valores
}
