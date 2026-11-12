// Tipo de entrevista (presencial / telefónica) — tipo_entrevista.js del sistema actual.
// Vistas: Departamentos (con rango de meses) · ODEI (por año) · ODEI y por mes.
// Niveles: ODEI → encuestador → conglomerado → vivienda - hogar.
import { FILTROS_RANGO, MESES, MESES_MAYUS, aniosEn, ambito, enlaceConglomerado, enlaceEncuestador,
  enlaceSede, entero, esSubsede, hastaMesActual, lineasPorMes, nav, num, rango } from './comun'

const SUFIJOS = ['Anterior', 'Actual']
const anioDe = (c, suf) => c.anio - (suf === 'Anterior' ? 1 : 0)
const esTotal = (f, i) => i === 0 || Number(f.id) === 0

const nombreAmbito = (c) => (c.vista === 'departamentos'
  ? 'ÁMBITO'
  : ['ODEI', 'ENCUESTADOR', 'CONGLOMERADO', 'VIVIENDA - HOGAR'][c.nivel - 1])

function celdasFijas(f, i, c) {
  const total = esTotal(f, i)
  if (c.vista === 'departamentos') return [{ texto: f.nombreMostrar, izquierda: true }]
  const n = { texto: total ? '' : f.id }
  if (c.nivel === 1) {
    const enlace = !total && !esSubsede(f.odei) && c.odeiPermitida(f.odei) ? enlaceSede(f.odei, f.nomodei) : null
    return [n, { texto: f.nomodei, izquierda: true, enlace }]
  }
  if (c.nivel === 2) {
    return [n, { texto: f.nomencue, izquierda: true, enlace: total ? null : enlaceEncuestador(f.codencue, f.nomencue) }]
  }
  if (c.nivel === 3) return [n, { texto: f.conglome, enlace: total ? null : enlaceConglomerado(f.conglome) }]
  return [n, { texto: total ? f.conglome : `${f.vivienda} - ${f.hogar}` }]
}

function tablaAnual(filas, c) {
  const anios = aniosEn(filas, /^entrevPres_(\d{4})$/)
  const conN = c.vista !== 'departamentos'
  return {
    fijas: conN ? 2 : 1,
    encabezados: [
      [...(conN ? [{ texto: 'N°', filas: 3 }] : []), { texto: nombreAmbito(c), filas: 3 },
        ...anios.map((a) => ({ texto: a, columnas: 4 }))],
      anios.flatMap(() => [{ texto: 'Presencial', columnas: 2 }, { texto: 'Telefónica', columnas: 2 }]),
      anios.flatMap(() => ['Abs.', '%', 'Abs.', '%'].map((t) => ({ texto: t }))),
    ],
    filas: filas.map((f, i) => ({
      total: esTotal(f, i),
      celdas: [...celdasFijas(f, i, c), ...anios.flatMap((a) => [
        { texto: entero(f[`entrevPres_${a}`]) }, { texto: num(f[`entrevPres_${a}porc`]) },
        { texto: entero(f[`entrevTelf_${a}`]) }, { texto: num(f[`entrevTelf_${a}porc`]) },
      ])],
    })),
  }
}

function tablaMensual(filas, c) {
  return {
    fijas: 2,
    encabezados: [
      [{ texto: 'N°', filas: 3 }, { texto: nombreAmbito(c), filas: 3 },
        ...SUFIJOS.map((s) => ({ texto: anioDe(c, s), columnas: 26 }))],
      SUFIJOS.flatMap(() => ['TOTAL', ...MESES_MAYUS].map((t) => ({ texto: t, columnas: 2 }))),
      SUFIJOS.flatMap(() => Array.from({ length: 13 }, () => [{ texto: 'Presencial' }, { texto: 'Telefónica' }]).flat()),
    ],
    filas: filas.map((f, i) => ({
      total: esTotal(f, i),
      celdas: [...celdasFijas(f, i, c), ...SUFIJOS.flatMap((suf) => [
        { texto: entero(f[`entrevPres_anio${suf}`]) }, { texto: entero(f[`entrevTelf_anio${suf}`]) },
        ...MESES.flatMap((m) => [{ texto: entero(f[`entrevPres_${m}${suf}`]) }, { texto: entero(f[`entrevTelf_${m}${suf}`]) }]),
      ])],
    })),
  }
}

function barrasPorTipo(f, anios) {
  const colores = ['#7CB5EC', '#434348', '#90ED7D', '#F7A35C', '#8085E9', '#F15C80', '#E4D354', '#2B908F']
  return {
    title: { text: 'TIPO DE ENTREVISTA', left: 'center', textStyle: { fontSize: 15 } },
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v == null ? '-' : `${Number(v).toFixed(1)}%`) },
    toolbox: { right: 10, feature: { saveAsImage: { title: 'Descargar' } } },
    legend: { bottom: 0 },
    grid: { left: 60, right: 20, top: 60, bottom: 60 },
    xAxis: { type: 'category', data: ['PRESENCIAL', 'TELEFÓNICA'] },
    yAxis: { type: 'value', name: 'ENTREVISTAS (%)', nameLocation: 'middle', nameGap: 42, max: 100 },
    series: anios.map((a, k) => ({
      name: String(a), type: 'bar', color: colores[k % colores.length],
      data: [f[`entrevPres_${a}porc`], f[`entrevTelf_${a}porc`]].map((v) => (v == null ? null : Number(v))),
      label: { show: true, position: 'top', fontSize: 10, formatter: (p) => (p.value == null ? '' : `${Number(p.value).toFixed(1)}%`) },
    })),
  }
}

export default {
  pantalla: 'tipo-entrevista',
  archivo: 'TIPO-DE-ENTREVISTA',
  colorEncabezado: '#1565C0',
  vistas: [
    { codigo: 'departamentos', nombre: 'Visualizar por Departamento' },
    { codigo: 'odei', nombre: 'Visualizar por ODEI' },
    { codigo: 'odei-mes', nombre: 'Visualizar por ODEI y por mes' },
  ],
  titulo: (c) => (c.vista === 'departamentos' ? 'TIPO DE ENTREVISTA' : `TIPO DE ENTREVISTA - ${ambito(c)}`),
  pestanas: () => [{ codigo: 'grafico', nombre: 'Resumen gráfica' }, { codigo: 'tabular', nombre: 'Resumen tabular' }],
  filtros: (c) => (c.vista === 'departamentos' ? FILTROS_RANGO : []),
  consulta: (c) => (c.vista === 'departamentos'
    ? { vista: 'departamentos', params: rango(c) }
    : { vista: c.vista, params: nav(c) }),
  tabla: (filas, c) => (c.vista === 'odei-mes' ? tablaMensual(filas, c) : tablaAnual(filas, c)),
  graficos: (filas, c) => {
    const f = filas[0]
    if (!f) return []
    if (c.vista !== 'odei-mes') return [{ opcion: barrasPorTipo(f, aniosEn(filas, /^entrevPres_(\d{4})$/)) }]
    const serie = (tipo, suf, nombre, color) => ({ nombre: `${nombre} ${anioDe(c, suf)}`, color,
      datos: hastaMesActual(MESES.map((m) => f[`entrev${tipo}_${m}${suf}`]), anioDe(c, suf)) })
    return [{ opcion: lineasPorMes({ titulo: 'TIPO DE ENTREVISTA', eje: 'Entrevistas', decimales: 0, series: [
      serie('Pres', 'Anterior', 'Presencial', '#F7A35C'), serie('Telf', 'Anterior', 'Telefónica', '#90ED7D'),
      serie('Pres', 'Actual', 'Presencial', '#7CB5EC'), serie('Telf', 'Actual', 'Telefónica', '#676C72'),
    ] }) }]
  },
  textos: [{
    descripcion: 'Este gráfico muestra los hogares entrevistados de forma presencial y mediante entrevista telefónica.',
    formula: 'Entrevista presencial = Hogares con visita de Cap. 601 y lugar de entrevista diferente de 3. Entrevista telefónica = Hogares con visita de Cap. 601 y lugar de entrevista igual a 3.',
  }],
}
