// Control de visitas (número de visitas y tiempo) — control_visita.js del sistema actual.
// Vistas: Departamentos · ODEI (por año) · ODEI y por mes · Casos.
// Cada año o mes lleva dos columnas: Promedio de visitas (veces) y Promedio de entrevista (minutos).
import { FILTROS_RANGO, MES3, MESES_MAYUS, aniosEn, ambito, barrasPorAnio, enlaceEncuestador, enlaceSede,
  esSubsede, hastaMesActual, lineasPorMes, nav, num, rango } from './comun'

const PAR = ['Promedio\nVisitas\n(veces)', 'Promedio\nEntrevista\n(minutos)']
const SUFIJOS = ['Anterior2', 'Anterior', 'Actual']

const sufijosDe = (c) => (c.nivel >= 3 ? ['Actual'] : SUFIJOS)
const anioDe = (c, suf) => c.anio - (suf === 'Anterior2' ? 2 : suf === 'Anterior' ? 1 : 0)
const vistaDatos = (c) => (c.vista === 'casos' ? 'casos' : c.vista)

function nombreColumna(c) {
  if (c.vista === 'departamentos') return 'Dominios de estudio'
  return ['ODEI', 'ENCUESTADOR', 'CONGLOMERADO'][c.nivel - 1]
}

// Primeras dos celdas de cada fila: N° y nombre (con enlace para bajar de nivel)
function celdasFijas(f, i, c, porMes) {
  const cod = porMes ? f.idMostrar : f.cododei
  if (c.nivel === 1) {
    const total = i === 0 || Number(cod) === 0
    const nombre = porMes ? f.nombreMostrar : f.nomOdei
    const enlace = c.vista !== 'departamentos' && !total && !esSubsede(cod) && c.odeiPermitida(cod)
      ? enlaceSede(cod, nombre) : null
    return [{ texto: total ? '' : cod }, { texto: nombre, izquierda: true, enlace }]
  }
  if (c.nivel === 2) {
    return [{ texto: i === 0 ? '' : f.id },
      { texto: f.encuestador, izquierda: true, enlace: i === 0 ? null : enlaceEncuestador(f.usuario, f.encuestador) }]
  }
  return [{ texto: i === 0 && porMes ? f.id : (i === 0 ? '' : f.id) }, { texto: i === 0 ? '' : f.conglomerado }]
}

function tablaPorAnio(filas, c) {
  const anios = aniosEn(filas, /^promVisitas(\d{4})$/)
  return {
    fijas: 2,
    encabezados: [
      [{ texto: 'N°', filas: 3 }, { texto: nombreColumna(c), filas: 3 }, { texto: 'AÑOS', columnas: anios.length * 2 }],
      anios.map((a) => ({ texto: a, columnas: 2 })),
      anios.flatMap(() => PAR.map((t) => ({ texto: t }))),
    ],
    filas: filas.map((f, i) => {
      const seccion = c.nivel === 1 && i !== 0 && Number(f.cododei) === 0
      return {
        total: i === 0 || seccion,
        celdas: [...celdasFijas(f, i, c, false),
          ...anios.flatMap((a) => [f[`promVisitas${a}`], f[`promDuracion${a}`]].map((v) => ({ texto: seccion ? '-' : num(v) })))],
      }
    }),
  }
}

function tablaPorMes(filas, c) {
  const sufijos = sufijosDe(c)
  const valores = (f, suf, m) => (m == null
    ? [f[`promVisitas_${suf}`], f[`promDuracion_${suf}`]]
    : [f[`promVisitas_${MES3[m]}${suf}`], f[`promDuracion_${MES3[m]}${suf}`]])
  return {
    fijas: 2,
    encabezados: [
      [{ texto: 'N°', filas: 3 }, { texto: nombreColumna(c), filas: 3 },
        ...sufijos.map((s) => ({ texto: anioDe(c, s), columnas: 26 }))],
      sufijos.flatMap(() => ['TOTAL', ...MESES_MAYUS].map((t) => ({ texto: t, columnas: 2 }))),
      sufijos.flatMap(() => Array.from({ length: 13 }, () => PAR.map((t) => ({ texto: t }))).flat()),
    ],
    filas: filas.map((f, i) => ({
      total: i === 0,
      celdas: [...celdasFijas(f, i, c, true),
        ...sufijos.flatMap((suf) => [null, ...MES3.keys()].flatMap((m) => valores(f, suf, m).map((v) => ({
          texto: num(v),
          // En el detalle de un encuestador, el mes del conglomerado va en rojo
          resaltado: c.nivel === 3 && m != null && Number(f.mes) === m + 1,
        }))))],
    })),
  }
}

function tablaCasos(filas) {
  const cols = [['id', 'N'], ['anio', 'Año'], ['odei', 'Cod. ODEI'], ['nomodei', 'ODEI'], ['mes', 'Mes'],
    ['periodo', 'Periodo'], ['conglome', 'Conglomerado'], ['codencue', 'DNI'], ['nomencue', 'Personal'],
    ['cantidad_hogares', 'Cantidad hogares'], ['cantidad_visitas', 'Cantidad visitas'],
    ['duracion_visitas', 'Duración visitas']]
  return {
    fijas: 0,
    encabezados: [[{ texto: 'Resumen de visitas a conglomerados', columnas: cols.length }],
      cols.map(([, t]) => ({ texto: t }))],
    filas: filas.map((f) => ({ celdas: cols.map(([k]) => ({ texto: f[k] ?? '', izquierda: k === 'nomencue' || k === 'nomodei' })) })),
  }
}

function nombreGrafico(filas, c) {
  if (c.nivel === 1) return filas[0]?.nomOdei ?? filas[0]?.nombreMostrar ?? 'NACIONAL'
  return c.nivel === 2 ? c.nombreSede : `${c.nombreSede} - ${c.encuestador}`
}

export default {
  pantalla: 'control-visitas',
  archivo: 'CONTROL-DE-VISITA',
  vistas: [
    { codigo: 'departamentos', nombre: 'Visualizar por Departamentos' },
    { codigo: 'odei', nombre: 'Visualizar por ODEI' },
    { codigo: 'odei-mes', nombre: 'Visualizar por ODEI y por mes' },
    { codigo: 'casos', nombre: 'Visualizar casos' },
  ],
  exclusiones: [{ v: 0, t: 'Sin exclusiones' }, { v: 1, t: 'Solo viviendas panel' }, { v: 2, t: 'Solo viviendas NO panel' }],
  usaComboOdei: true,
  titulo: (c) => (c.vista === 'casos' ? 'CONTROL DE VISITA' : `CONTROL DE VISITA - ${ambito(c)}`),
  pestanas: (c) => (c.vista === 'casos'
    ? [{ codigo: 'tabular', nombre: 'Resumen tabular' }]
    : [{ codigo: 'grafico', nombre: 'Resumen gráfico' }, { codigo: 'tabular', nombre: 'Resumen tabular' }]),
  // Como la pantalla actual: los filtros están en la pestaña tabular
  filtros: (c) => {
    if (c.pestana === 'grafico' && c.vista !== 'casos') return []
    if (c.vista === 'departamentos') return FILTROS_RANGO
    if (c.vista === 'odei-mes') return [...FILTROS_RANGO, 'excluir']
    if (c.vista === 'casos') return [...FILTROS_RANGO, 'sede']
    return []
  },
  consulta: (c) => {
    const v = vistaDatos(c)
    if (v === 'departamentos') return { vista: v, params: rango(c) }
    if (v === 'odei') return { vista: v, params: nav(c) }
    if (v === 'odei-mes') return { vista: v, params: { ...nav(c), ...rango(c), excluir: c.filtros.excluir } }
    return { vista: 'casos', params: { sede: String(c.filtros.sede ?? 0), ...rango(c) } }
  },
  tabla: (filas, c) => {
    if (c.vista === 'casos') return tablaCasos(filas)
    return c.vista === 'odei-mes' ? tablaPorMes(filas, c) : tablaPorAnio(filas, c)
  },
  graficos: (filas, c) => {
    const f = filas[0]
    if (!f || c.vista === 'casos') return []
    const nombre = nombreGrafico(filas, c)
    if (c.vista !== 'odei-mes') {
      const anios = aniosEn(filas, /^promVisitas(\d{4})$/)
      return [
        { ancho: 'medio', opcion: barrasPorAnio({ titulo: `PROMEDIO DE VISITAS\n${nombre}`, subtitulo: '(Número de veces)',
          eje: 'Número de Visitas', nombre: 'Visitas', anios, valores: anios.map((a) => f[`promVisitas${a}`]), colores: '#7CB5EC' }) },
        { ancho: 'medio', opcion: barrasPorAnio({ titulo: `TIEMPO PROMEDIO DE ENTREVISTA\n${nombre}`, subtitulo: '(Minutos)',
          eje: 'Duración en minutos', nombre: 'Duración', anios, valores: anios.map((a) => f[`promDuracion${a}`]),
          colores: '#7CB5EC', decimales: 0 }) },
      ]
    }
    const colores = { Anterior2: '#FF0000', Anterior: '#489CDF', Actual: '#000000' }
    const series = (metrica) => sufijosDe(c).map((suf) => ({
      nombre: String(anioDe(c, suf)), color: colores[suf],
      datos: hastaMesActual(MES3.map((m) => f[`${metrica}_${m}${suf}`]), anioDe(c, suf)),
    }))
    return [
      { ancho: 'medio', opcion: lineasPorMes({ titulo: `PROMEDIO DE VISITAS\n${nombre}`, subtitulo: '(Número de veces)',
        eje: 'Número de Visitas', series: series('promVisitas') }) },
      { ancho: 'medio', opcion: lineasPorMes({ titulo: `TIEMPO PROMEDIO DE ENTREVISTA\n${nombre}`, subtitulo: '(Minutos)',
        eje: 'Duración en minutos', series: series('promDuracion') }) },
    ]
  },
  textos: [
    { descripcion: 'Es el numero promedio de visitas que la encuestadora realiza en el hogar hasta completar la información (número de veces).',
      formula: 'Prom. Visitas = Total Visitas al Hogar / Total de Hogares Visitados' },
    { descripcion: 'Es el tiempo promedio que el encuestador utiliza para completar la información de los hogares, se considera el tiempo de cada visita que la encuestadora realiza al hogar de las viviendas completas e incompletas (Expresado en minutos).',
      formula: 'Prom. Entrev = Total Tiempo (Minutos) de visitas al hogar / Total de Hogares Entrevistados' },
  ],
}
