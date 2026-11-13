// Esquema común de las pantallas de indicadores de calidad (viviendaHogar.js,
// seguimientoProgramasSociales.js, ... del sistema actual): combo de indicadores, vistas por
// Departamentos / ODEI / ODEI y por mes (y "Visualizar casos" en algunos indicadores),
// gráfico de barras por año o de líneas por mes, y objetivo y fórmula en un cuadro.
//
// Columnas que devuelve el procedimiento enaho2017_calidad_{indicador}{vista}:
//   por año:  indicador2013 … indicador{año}, Estado
//   por mes:  indicadorAnterior2 / indicadorAnterior / indicadorActual (total del año) y
//             {enero..diciembre}{Anterior2|Anterior|Actual}
// Los años salen de los datos: no hay que tocar código al cambiar de año.
import { FILTROS_RANGO, MESES, MESES_CORTOS, aniosEn, barrasPorAnio, enlaceConglomerado, enlaceEncuestador,
  enlaceSede, esSubsede, hastaMesActual, lineasPorMes, nav, num, rango } from '../reportesCobertura/comun'

const SUFIJOS = ['Anterior2', 'Anterior', 'Actual']
const COLOR_SUFIJO = { Anterior2: '#FF0000', Anterior: '#489CDF', Actual: '#000000' }
const anioDe = (c, suf) => c.anio - (suf === 'Anterior2' ? 2 : suf === 'Anterior' ? 1 : 0)
const PATRON_ANIO = /^indicador(\d{4})$/
const MESES_TITULO = ['Seleccione', ...MESES.map((m) => m.toUpperCase())]

// Cada pantalla actual tiene su propia lista de exclusiones (mismo código, textos distintos)
export const EXCLUSIONES_CALIDAD = [
  { v: 0, t: 'Sin exclusiones' }, { v: 1, t: 'Solo viviendas panel' }, { v: 2, t: 'Solo viviendas NO panel' },
  { v: 3, t: 'Conglomerados panel' },
]
export const EXCLUSIONES_SEGUIMIENTO = [
  { v: 0, t: 'Sin exclusiones' }, { v: 1, t: 'Excluir no panel' }, { v: 2, t: 'Excluir panel' },
  { v: 3, t: 'Excluir panel con resultado ausente y subresultado no tiene teléfono' },
]
export const EXCLUSIONES_EMPLEO = [
  { v: 0, t: 'Sin exclusiones' }, { v: 1, t: 'Excluir no panel' }, { v: 2, t: 'Excluir panel' },
  { v: 3, t: 'Conglomerados panel' },
]

const esTotal = (f, i) => i === 0 || (f.idMostrar != null && Number(f.idMostrar) === 0)

// "1. Promedio de habitaciones por vivienda." → "Promedio de habitaciones por vivienda"
const sinNumero = (t) => t.replace(/^\d+\.\s*/, '').replace(/\.$/, '')

function nombreColumna(c) {
  if (c.vista === 'departamentos') return 'Dominios de Estudio'
  return ['ODEI', 'ENCUESTADOR', 'CONGLOMERADO'][c.nivel - 1]
}

// N° y nombre de la fila, con el enlace para bajar de nivel
function celdasFijas(f, i, c) {
  if (c.nivel === 1) {
    const total = esTotal(f, i)
    const enlace = c.vista !== 'departamentos' && i > 0 && !esSubsede(f.idMostrar) && !total
      && c.odeiPermitida(f.idMostrar) ? enlaceSede(f.idMostrar, f.nombreMostrar) : null
    return [{ texto: total ? '' : f.idMostrar }, { texto: f.nombreMostrar, izquierda: true, enlace }]
  }
  const n = { texto: i === 0 ? '' : f.id }
  if (c.nivel === 2) {
    return [n, { texto: f.encuestador, izquierda: true,
      enlace: i === 0 ? null : enlaceEncuestador(f.usuario, f.encuestador) }]
  }
  // Por año el conglomerado no tiene detalle; por mes baja a las viviendas
  const enlace = c.vista === 'odei-mes' && i > 0 ? enlaceConglomerado(f.conglomerado) : null
  return [n, { texto: i === 0 && c.vista !== 'odei-mes' ? '' : f.conglomerado, izquierda: c.vista === 'odei-mes', enlace }]
}

function tablaPorAnio(filas, c) {
  const anios = aniosEn(filas, PATRON_ANIO)
  // "Estado" (Aceptable / Revisar) solo si el procedimiento lo devuelve (vivienda, demográficos...)
  const conEstado = c.nivel === 1 && filas.some((f) => 'Estado' in f)
  const decimales = c.nivel === 1 ? 2 : 1
  return {
    fijas: 2,
    encabezados: [
      [{ texto: 'N°', filas: 2 }, { texto: nombreColumna(c), filas: 2 },
        { texto: 'AÑOS', columnas: anios.length + (conEstado ? 1 : 0) }],
      [...anios.map((a) => ({ texto: a })), ...(conEstado ? [{ texto: 'Estado' }] : [])],
    ],
    filas: filas.map((f, i) => {
      // Filas de sección (URBANO, RURAL, LIMA METROPOLITANA...): sin valores, como la pantalla actual
      const seccion = c.nivel === 1 && i !== 0 && esTotal(f, i)
      return {
        total: esTotal(f, i),
        celdas: [...celdasFijas(f, i, c),
          ...anios.map((a) => ({ texto: seccion ? '-' : num(f[`indicador${a}`], decimales) })),
          ...(conEstado ? [{ texto: seccion ? '-' : (f.Estado ?? '') }] : [])],
      }
    }),
  }
}

function tablaPorMes(filas, c) {
  if (c.nivel >= 4) {
    return {
      fijas: 0,
      encabezados: [['N°', 'MES', 'CONGLOMERADO', 'VIVIENDA', 'HOGAR', String(c.anio)].map((t) => ({ texto: t }))],
      filas: filas.map((f, i) => ({
        total: i === 0,
        celdas: [...(i === 0 ? ['', '', '', '', ''] : [f.id, f.mes, f.conglomerado, f.vivienda, f.hogar])
          .map((t) => ({ texto: t ?? '' })), { texto: num(f.indicadorActual) }],
      })),
    }
  }
  const sufijos = c.nivel >= 3 ? ['Actual'] : SUFIJOS
  return {
    fijas: 2,
    encabezados: [
      [{ texto: 'N°', filas: 3 }, { texto: nombreColumna(c), filas: 3 }, { texto: 'AÑOS', columnas: sufijos.length * 13 }],
      sufijos.map((s) => ({ texto: anioDe(c, s), columnas: 13 })),
      sufijos.flatMap(() => ['Total', ...MESES_CORTOS].map((t) => ({ texto: t }))),
    ],
    filas: filas.map((f, i) => ({
      total: esTotal(f, i),
      celdas: [...celdasFijas(f, i, c), ...sufijos.flatMap((suf) => [
        { texto: num(f[`indicador${suf}`]) },
        ...MESES.map((m, k) => ({ texto: num(f[`${m}${suf}`]),
          // En el detalle de un encuestador, el mes del conglomerado va en rojo
          resaltado: c.nivel === 3 && Number(f.mes) === k + 1 })),
      ])],
    })),
  }
}

// Casos (balance del hogar): todas las columnas que devuelve el procedimiento, en su orden
function tablaCasos(filas, c, ind) {
  const cols = ind.casos.columnas
  return {
    fijas: 0,
    encabezados: [[{ texto: ind.casos.titulo, columnas: cols.length }], cols.map(([, t]) => ({ texto: t }))],
    filas: filas.map((f) => ({ celdas: cols.map(([k]) => ({ texto: f[k] ?? '', izquierda: k === 'nomencue' })) })),
  }
}

// Los nombres de indicador son largos: el título se parte en varias líneas si no entra
function tituloLargo(opcion) {
  opcion.title.textStyle = { ...opcion.title.textStyle, width: 820, overflow: 'break', fontSize: 14 }
  opcion.grid.top += 20
  return opcion
}

function subtituloFiltros(c) {
  const f = c.filtros
  return `mes inicial: ${MESES_TITULO[f.mes_inicio]} - periodo inicial: ${f.periodo_inicio || 'TODOS'} - `
    + `mes final: ${MESES_TITULO[f.mes_fin]} - periodo final: ${f.periodo_fin || 'TODOS'}`
}

// Exportados para los indicadores con estructura propia (config/reportesCalidad/especiales/*)
export { esTotal, celdasFijas, tituloLargo, subtituloFiltros, sinNumero, anioDe, SUFIJOS, COLOR_SUFIJO, nombreColumna,
  tablaPorMes, tablaCasos }

/** Código que se consulta: el del combo de razones (salud) o el del indicador. */
export function codigoConsulta(c, ind) {
  const sub = ind.subindicadores?.find((x) => String(x.v) === String(c.query?.sub))
  return sub ? sub.v : c.indicador
}

/**
 * Configuración de una pantalla de indicadores de calidad.
 * indicadores: [{ v: código, t: '1. Nombre.', unidad: '%' | '', descripcion, formula,
 *                 casos?: { titulo, columnas: [[clave, encabezado]] },
 *                 subindicadores?: [{ v, t, descripcion, formula }]   (combo "RAZONES:")
 *                 exclusiones?: [...]                                 (si cambian)
 *                 especial?: { vistas, pestanas, filtros, consulta, tabla, graficos, textos,
 *                              migas, selectores }  (reemplazan lo común; ver especiales/) }]
 */
export function pantallaCalidad({ pantalla, titulo, archivo, indicadores, exclusiones = EXCLUSIONES_CALIDAD,
  conAmbito = true }) {
  const indicadorDe = (c) => indicadores.find((i) => i.v === c.indicador) ?? indicadores[0]
  // Lo propio del indicador (si lo tiene) o lo común
  const de = (nombre, comun) => (...args) => {
    const c = args[args.length - 1]
    const e = indicadorDe(c).especial
    return e?.[nombre] ? e[nombre](...args, { titulo, indicadorDe }) : comun(...args)
  }
  const ambito = (c) => (c.nivel === 1 ? 'ÁMBITO NACIONAL' : `SEDE ${c.nombreSede || c.sede}`)
  // Nombre del indicador (o de la razón elegida) para títulos de gráfico y Excel
  const nombreDe = (c) => {
    const ind = indicadorDe(c)
    return ind.subindicadores?.find((x) => x.v === codigoConsulta(c, ind) && x.v !== ind.v)?.t ?? ind.t
  }

  return {
    pantalla,
    archivo,
    indicadores,
    exclusiones: (c) => indicadorDe(c).exclusiones ?? exclusiones,
    usaComboOdei: true,
    textosEnCuadro: true,
    // Precios: ODEI de la lista (sin "TODOS") y enero del año en curso, como la pantalla actual
    filtrosIniciales: { departamento: '00', anio: new Date().getFullYear(), odei: 1, mes_precios: 1 },
    titulo: de('titulo', (c) => (c.vista === 'casos' || !conAmbito ? titulo : `${titulo} - ${ambito(c)}`)),
    // El Excel lleva también el indicador elegido, como la pantalla actual
    tituloExcel: (c) => `${titulo} - ${nombreDe(c)}${c.vista === 'casos' ? '' : ` - ${ambito(c)}`}`,
    selectores: (c) => {
      const ind = indicadorDe(c)
      if (ind.especial?.selectores) return ind.especial.selectores(c)
      return ind.subindicadores ? [{ clave: 'sub', etiqueta: 'RAZONES:', opciones: ind.subindicadores }] : []
    },
    migas: (c) => indicadorDe(c).especial?.migas?.(c) ?? null,
    vistas: de('vistas', (c) => [
      { codigo: 'departamentos', nombre: 'Visualizar por Departamentos' },
      { codigo: 'odei', nombre: 'Visualizar por ODEI' },
      { codigo: 'odei-mes', nombre: 'Visualizar por ODEI y por mes' },
      ...(indicadorDe(c).casos ? [{ codigo: 'casos', nombre: 'Visualizar casos' }] : []),
    ]),
    pestanas: de('pestanas', (c) => (c.vista === 'casos'
      ? [{ codigo: 'tabular', nombre: 'Resumen tabular' }]
      : [{ codigo: 'grafico', nombre: 'Resumen gráfico' }, { codigo: 'tabular', nombre: 'Resumen tabular' }])),
    filtros: de('filtros', (c) => {
      if (c.vista === 'odei-mes') return [...FILTROS_RANGO, 'excluir']
      if (c.vista === 'casos') return ['sede', ...FILTROS_RANGO]
      return []
    }),
    consulta: de('consulta', (c) => {
      const base = { indicador: codigoConsulta(c, indicadorDe(c)) }
      if (c.vista === 'departamentos') return { vista: c.vista, params: base }
      if (c.vista === 'odei') return { vista: c.vista, params: { ...base, ...nav(c) } }
      if (c.vista === 'odei-mes') {
        return { vista: c.vista, params: { ...base, ...nav(c), ...rango(c), excluir: c.filtros.excluir } }
      }
      return { vista: 'casos', params: { ...base, odei: String(c.filtros.sede ?? 0), ...rango(c) } }
    }),
    tabla: de('tabla', (filas, c) => {
      if (c.vista === 'casos') return tablaCasos(filas, c, indicadorDe(c))
      return c.vista === 'odei-mes' ? tablaPorMes(filas, c) : tablaPorAnio(filas, c)
    }),
    graficos: de('graficos', (filas, c) => {
      const f = filas[0]
      if (!f || c.vista === 'casos' || (c.vista === 'odei-mes' && c.nivel >= 4)) return []
      const ind = indicadorDe(c)
      const nombreFila = c.nivel === 1 ? f.nombreMostrar : (filas[1]?.nombreMostrar ?? c.nombreSede)
      const tituloGrafico = `${nombreDe(c)} - ${c.nivel >= 3 ? `${nombreFila} / ${c.encuestador}` : nombreFila}`
      const eje = sinNumero(ind.t)
      if (c.vista !== 'odei-mes') {
        const anios = aniosEn(filas, PATRON_ANIO)
        return [{ alto: 480, opcion: tituloLargo(barrasPorAnio({ titulo: tituloGrafico, eje, nombre: 'Año', anios,
          valores: anios.map((a) => f[`indicador${a}`]), sufijo: ind.unidad ? ` ${ind.unidad}` : '',
          colores: anios.map((_, k) => (k === anios.length - 1 ? '#B38B8B' : '#E0B7B7')) })) }]
      }
      const sufijos = c.nivel >= 3 ? ['Actual'] : SUFIJOS
      return [{ alto: 480, opcion: tituloLargo(lineasPorMes({ titulo: tituloGrafico, subtitulo: subtituloFiltros(c), eje,
        series: sufijos.map((suf) => ({ nombre: String(anioDe(c, suf)), color: COLOR_SUFIJO[suf],
          datos: hastaMesActual(MESES.map((m) => f[`${m}${suf}`]), anioDe(c, suf)) })) })) }]
    }),
    textos: de('textos', (c) => {
      const ind = indicadorDe(c)
      const sub = ind.subindicadores?.find((x) => x.v === codigoConsulta(c, ind))
      const t = sub?.descripcion ? sub : ind
      return t.descripcion || t.formula ? [{ descripcion: t.descripcion, formula: t.formula }] : []
    }),
  }
}
