// Reglas de la pantalla TNR según estrato (tnr_estrato.js del sistema actual):
// qué nombre lleva cada fila, a dónde lleva su enlace y cómo se arman las columnas.

export const MESES_CORTOS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Dic']
export const ESTRATOS = { 1: 'A (mas alto)', 2: 'B', 3: 'C', 4: 'D', 5: 'E (mas bajo)' }
export const AREAS = { 1: 'TOTAL URBANO', 2: 'LIMA METROPOLITANA', 3: 'RESTO URBANO' }

const orden = (fila) => Number(fila.ORDEN ?? 0)
/** Filas de área (total urbano, Lima Metropolitana, resto urbano) en el nivel nacional. */
export const esArea = (fila) => [0, 6, 12].includes(orden(fila))
/** Fila resaltada en amarillo: ORDEN 0. */
export const esTotal = (fila) => orden(fila) === 0
/** Área de un estrato según su ORDEN: 1-5 total urbano, 7-11 Lima Metropolitana, 13-17 resto. */
export const areaDeOrden = (o) => (o <= 5 ? 1 : o <= 11 ? 2 : 3)

/** Años con columnas TNR2017, TNR2018, ... (salen de los datos). */
export function aniosEstrato(filas) {
  const anios = new Set()
  filas.forEach((f) => Object.keys(f).forEach((k) => {
    const m = k.match(/^TNR(\d{4})$/)
    if (m) anios.add(Number(m[1]))
  }))
  return [...anios].sort((a, b) => a - b)
}

/** Las 6 columnas de cada año. TOTAL_ABS = panel + no panel, como la pantalla actual. */
export function valoresAnio(fila, a) {
  const p = fila[`TNR${a}P_ABS`]
  const np = fila[`TNR${a}NP_ABS`]
  const total = p == null && np == null ? null : Number(p ?? 0) + Number(np ?? 0)
  return [
    { v: fila[`TNR${a}`], tasa: true }, { v: total }, { v: fila[`TNR${a}P`], tasa: true },
    { v: p }, { v: fila[`TNR${a}NP`], tasa: true }, { v: np },
  ]
}

/** Columnas de la tabla por mes: TOTAL y, por PANEL y NO PANEL, total + 12 meses con Abs. */
export function valoresMes(fila) {
  const vals = [{ v: fila.TNR, tasa: true }]
  for (const g of ['P', 'NP']) {
    vals.push({ v: fila[`TNR${g}`], tasa: true }, { v: fila[`TNR${g}_ABS`] })
    for (let m = 1; m <= 12; m++) vals.push({ v: fila[`TNR${g}_${m}`], tasa: true }, { v: fila[`TNR${g}_${m}_ABS`] })
  }
  return vals
}

export function formatear(valor, esTasa) {
  if (valor === null || valor === undefined || valor === '') return '-'
  const n = Number(valor)
  if (Number.isNaN(n)) return String(valor)
  return esTasa ? n.toFixed(1) : String(n)
}

/**
 * Series del gráfico de un área: una serie por año, cinco barras (estratos A..E).
 * Toma las filas del nivel nacional (ORDEN 1-5, 7-11 y 13-17).
 */
export function seriesArea(filas, area) {
  const desde = (area - 1) * 6 + 1
  const estratos = [0, 1, 2, 3, 4].map((k) => filas.find((f) => orden(f) === desde + k))
  return aniosEstrato(filas).map((a) => ({
    name: String(a),
    data: estratos.map((f) => (f && f[`TNR${a}`] != null ? Number(f[`TNR${a}`]) : null)),
  }))
}
