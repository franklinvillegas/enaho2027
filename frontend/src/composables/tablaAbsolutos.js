// Tabla de valores absolutos por encuestador (información indirecta, vista por ODEI y mes,
// al entrar a una sede). Columnas como la pantalla actual: ENCUESTADOR | ACTIVO | por año:
// Ind. y Total, y por mes Ind. y Tot. Los años salen de los datos (indirecta2025, ...).

const MESES_ABS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic']
const MESES_CORTOS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Dic']

export function aniosAbsolutos(filas) {
  const anios = new Set()
  filas.forEach((f) => Object.keys(f).forEach((k) => {
    const m = k.match(/^indirecta(\d{4})$/)
    if (m) anios.add(Number(m[1]))
  }))
  return [...anios].sort((a, b) => a - b)
}

/** Claves de cada año, en el orden de las columnas. */
export function clavesAnio(a) {
  return [`indirecta${a}`, `tot${a}`, ...MESES_ABS.flatMap((m, i) => [`ind_${m}${a}`, `tot${a}_${i + 1}`])]
}

export { MESES_CORTOS }
