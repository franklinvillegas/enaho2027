// Piezas comunes de las configuraciones de reportes de cobertura.

export const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre',
  'octubre', 'noviembre', 'diciembre']
export const MESES_CORTOS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Dic']
export const MESES_MAYUS = MESES.map((m) => m.toUpperCase())
export const MES3 = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic']

/** Número con decimales fijos; vacío o no numérico se muestra como "-" o tal cual. */
export function num(valor, decimales = 1) {
  if (valor === null || valor === undefined || valor === '') return '-'
  const n = Number(valor)
  return Number.isNaN(n) ? String(valor) : n.toFixed(decimales)
}
export const entero = (valor) => (valor === null || valor === undefined || valor === '' ? '-' : String(valor))

/** Parámetros de navegación + rango de meses y periodos ya aplicados. */
export const nav = (c) => ({ sede: c.sede, usuario: c.usuario, conglomerado: c.conglomerado })
export const rango = (c) => ({ mes_inicio: c.filtros.mes_inicio, mes_fin: c.filtros.mes_fin,
  periodo_inicio: c.filtros.periodo_inicio, periodo_fin: c.filtros.periodo_fin })
export const FILTROS_RANGO = ['mes_inicio', 'periodo_inicio', 'mes_fin', 'periodo_fin']

/** Texto del ámbito para el título: ÁMBITO NACIONAL / SEDE X / SEDE X - ENCUESTADOR Y ... */
export function ambito(c) {
  if (c.nivel === 1) return 'ÁMBITO NACIONAL'
  let t = `SEDE ${c.nombreSede || c.sede}`
  if (c.nivel >= 3) t += ` - ENCUESTADOR ${c.encuestador || c.usuario}`
  if (c.nivel >= 4) t += ` - CONGLOMERADO ${c.conglomerado}`
  return t
}

/** Las sedes 15.1, 15.2 y 15.3 (Lima) no tienen detalle en la pantalla actual. */
export const esSubsede = (codigo) => String(codigo ?? '').includes('.')

export const enlaceSede = (codigo, nombre) => ({ sede: String(codigo), nombreSede: nombre })
export const enlaceEncuestador = (usuario, nombre) => ({ usuario: String(usuario), encuestador: nombre })
export const enlaceConglomerado = (conglomerado) => ({ conglomerado: String(conglomerado) })

/** Años presentes en las columnas que cumplen el patrón (ej. /^promVisitas(\d{4})$/). */
export function aniosEn(filas, patron) {
  const anios = new Set()
  filas.forEach((f) => Object.keys(f).forEach((k) => {
    const m = k.match(patron)
    if (m) anios.add(Number(m[1]))
  }))
  return [...anios].sort((a, b) => a - b)
}

/** Corta los meses que aún no llegan en el año en curso (como la pantalla actual). */
export const hastaMesActual = (valores, anio, hoy = new Date()) =>
  (anio === hoy.getFullYear() ? valores.slice(0, hoy.getMonth() + 1) : valores)

/** Gráfico de barras por año, con la etiqueta de valor encima de cada barra. */
export function barrasPorAnio({ titulo, subtitulo, eje, nombre, anios, valores, colores, decimales = 1, sufijo = '' }) {
  return {
    title: { text: titulo, subtext: subtitulo, left: 'center', textStyle: { fontSize: 15 } },
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v == null ? '-' : `${Number(v).toFixed(decimales)}${sufijo}`) },
    toolbox: { right: 10, feature: { saveAsImage: { title: 'Descargar' } } },
    grid: { left: 60, right: 20, top: subtitulo ? 80 : 60, bottom: 40 },
    xAxis: { type: 'category', data: anios.map(String) },
    yAxis: { type: 'value', name: eje, nameLocation: 'middle', nameGap: 42, max: (v) => Math.ceil(v.max * 1.2) },
    series: [{ name: nombre, type: 'bar', barWidth: '55%',
      data: valores.map((v, k) => ({ value: v == null ? null : Number(v),
        itemStyle: { color: Array.isArray(colores) ? colores[k] : colores } })),
      label: { show: true, position: 'top', fontSize: 11, fontWeight: 'bold',
        formatter: (p) => (p.value == null ? '' : `${Number(p.value).toFixed(decimales)}${sufijo}`) } }],
  }
}

/** Gráfico de líneas por mes, una serie por año (o por tipo). */
export function lineasPorMes({ titulo, subtitulo, eje, series, decimales = 1 }) {
  return {
    title: { text: titulo, subtext: subtitulo, left: 'center', textStyle: { fontSize: 15 } },
    tooltip: { trigger: 'axis' },
    toolbox: { right: 10, feature: { saveAsImage: { title: 'Descargar' } } },
    legend: { bottom: 0 },
    grid: { left: 60, right: 30, top: subtitulo ? 80 : 60, bottom: 60 },
    xAxis: { type: 'category', data: MESES_CORTOS },
    yAxis: { type: 'value', name: eje, nameLocation: 'middle', nameGap: 42 },
    series: series.map((s) => ({ name: s.nombre, type: 'line', color: s.color, symbolSize: 7,
      data: s.datos.map((v) => (v == null ? null : Number(v))),
      label: { show: true, fontSize: 10, formatter: (p) => (p.value == null ? '' : Number(p.value).toFixed(decimales)) } })),
  }
}
