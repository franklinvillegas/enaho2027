// Omisión por capítulos — omision_capitulo.js del sistema actual.
// Pestañas: gráfico · tabular por año · tabular por mes · mapa de calor.
// Cada capítulo es un grupo de columnas: los años anteriores se abren y cierran con ±
// (como la pantalla actual); el año en curso siempre se ve. En la tabla por mes cada mes
// se abre para ver sus capítulos.
import { FILTROS_RANGO, MESES_CORTOS, ambito, barrasPorAnio, enlaceEncuestador, enlaceSede, entero, esSubsede,
  nav, num, rango } from './comun'

const CAPITULOS = [
  ['TOTAL', 'Omisión Total'], ['700', 'Omisión 700'], ['710', '700a'], ['602M', '602'], ['602AM', '602a'],
  ['603M', '603'], ['604M', '604'], ['605M', '605'], ['606M', '606'], ['606DM', '606d'], ['607M', '607'],
  ['609M', '609'], ['610M', '610'], ['611M', '611'], ['612M', '612'], ['GOBER', 'Gobernabilidad'],
  ['CORRUP', 'Corrupción'], ['ALIM', 'Alimentaria'],
]
const CORTOS = { TOTAL: 'Total', GOBER: 'Gober.', CORRUP: 'Corrup.', ALIM: 'Alim.' }
const corto = (cap, nombre) => CORTOS[cap] ?? nombre

const grupoAnio = (cap) => `a-${cap}`
const grupoMes = (m) => `m-${m}`
const mm = (m) => String(m).padStart(2, '0')

function aniosDe(filas) {
  const anios = new Set()
  filas.forEach((f) => Object.keys(f).forEach((k) => {
    const x = k.match(/^OMI_(\d{4})_TOTAL$/)
    if (x) anios.add(Number(x[1]))
  }))
  return [...anios].sort((a, b) => a - b)
}

const nombreAmbito = (c) => ['ODEI', 'ENCUESTADOR', 'CONGLOMERADO', 'CONGLOMERADO'][c.nivel - 1]

function celdasFijas(f, i, c) {
  const total = i === 0 || Number(f.ID) === 0
  if (c.nivel === 1) {
    const enlace = !total && !esSubsede(f.CODODEI) && c.odeiPermitida(f.CODODEI) ? enlaceSede(f.CODODEI, f.ODEI) : null
    return [{ texto: total ? '' : f.ID }, { texto: f.ODEI, izquierda: true, enlace }]
  }
  if (c.nivel === 2) {
    return [{ texto: total ? '' : f.ID },
      { texto: f.NOMENCUE, izquierda: true, enlace: total ? null : enlaceEncuestador(f.CODENCUE, f.NOMENCUE) }]
  }
  return [{ texto: total ? '' : f.ID }, { texto: f.CONGLOME }]
}

function tablaAnio(filas, c) {
  const anios = aniosDe(filas)
  const actual = anios[anios.length - 1]
  const previos = anios.slice(0, -1)
  return {
    fijas: 2,
    encabezados: [
      [{ texto: 'ID', filas: 3 }, { texto: nombreAmbito(c), filas: 3 },
        ...CAPITULOS.map(([cap, nombre]) => ({ texto: nombre, columnas: anios.length * 2, columnasCerrado: 2,
          alternar: grupoAnio(cap) }))],
      CAPITULOS.flatMap(([cap]) => [...previos.map((a) => ({ texto: a, columnas: 2, grupo: grupoAnio(cap) })),
        { texto: actual, columnas: 2 }]),
      CAPITULOS.flatMap(([cap]) => anios.flatMap((a) => ['%', 'Abs.'].map((t) => ({ texto: t,
        grupo: a === actual ? undefined : grupoAnio(cap) })))),
    ],
    filas: filas.map((f, i) => ({
      total: i === 0 || Number(f.ID) === 0,
      celdas: [...celdasFijas(f, i, c),
        ...CAPITULOS.flatMap(([cap]) => anios.flatMap((a) => {
          const grupo = a === actual ? undefined : grupoAnio(cap)
          return [{ texto: num(f[`OMI_${a}_${cap}`]), grupo }, { texto: entero(f[`OMI_${a}_${cap}_ABS`]), grupo }]
        }))],
    })),
  }
}

function tablaMes(filas, c) {
  const meses = Array.from({ length: 12 }, (_, k) => k + 1)
  return {
    fijas: 2,
    encabezados: [
      [{ texto: 'ID', filas: 3 }, { texto: nombreAmbito(c), filas: 3 }, { texto: 'TOTAL', columnas: 2, filas: 2 },
        ...meses.map((m) => ({ texto: MESES_CORTOS[m - 1], columnas: CAPITULOS.length * 2, columnasCerrado: 2,
          alternar: grupoMes(m) }))],
      meses.flatMap((m) => CAPITULOS.map(([cap, nombre]) => ({ texto: corto(cap, nombre), columnas: 2,
        grupo: cap === 'TOTAL' ? undefined : grupoMes(m) }))),
      [{ texto: '%' }, { texto: 'Abs.' }, ...meses.flatMap((m) => CAPITULOS.flatMap(([cap]) => ['%', 'Abs.'].map((t) => ({
        texto: t, grupo: cap === 'TOTAL' ? undefined : grupoMes(m) }))))],
    ],
    filas: filas.map((f, i) => ({
      total: i === 0 || Number(f.ID) === 0,
      celdas: [...celdasFijas(f, i, c),
        { texto: num(f.OMI_00_TOTAL) }, { texto: entero(f.OMI_00_TOTAL_ABS) },
        ...meses.flatMap((m) => CAPITULOS.flatMap(([cap]) => {
          const grupo = cap === 'TOTAL' ? undefined : grupoMes(m)
          // En el detalle de un encuestador, el mes del conglomerado va en rojo
          const resaltado = c.nivel >= 3 && Number(f.MES) === m
          return [{ texto: num(f[`OMI_${mm(m)}_${cap}`]), grupo, resaltado },
            { texto: entero(f[`OMI_${mm(m)}_${cap}_ABS`]), grupo, resaltado }]
        }))],
    })),
  }
}

function nombreGrafico(c) {
  if (c.nivel === 1) return 'NACIONAL'
  return c.nivel === 2 ? c.nombreSede || c.sede : `${c.nombreSede || c.sede} - ${c.encuestador || c.usuario}`
}

export default {
  pantalla: 'omision-capitulos',
  archivo: 'OMISION-POR-CAPITULOS',
  colorEncabezado: '#1565C0',
  // Al entrar solo se ve el año en curso de cada capítulo y el total de cada mes
  gruposCerrados: [...CAPITULOS.map(([cap]) => grupoAnio(cap)),
    ...Array.from({ length: 12 }, (_, k) => grupoMes(k + 1))],
  titulo: (c) => `OMISIÓN POR CAPÍTULOS - ${ambito(c)}`,
  pestanas: () => [
    { codigo: 'grafico', nombre: 'Resumen gráfico' },
    { codigo: 'anio', nombre: 'Resumen tabular omisión por año' },
    { codigo: 'mes', nombre: 'Resumen tabular omisión por mes' },
    { codigo: 'mapa', nombre: 'Mapa de calor' },
  ],
  filtros: (c) => (c.pestana === 'mes' ? FILTROS_RANGO : []),
  consulta: (c) => {
    const p = { sede: c.sede, usuario: c.usuario }
    if (c.pestana === 'mapa') return null
    if (c.pestana === 'anio') return { vista: 'anio', params: p }
    if (c.pestana === 'mes') return { vista: 'mes', params: { ...nav(c), ...rango(c) } }
    return { vista: 'grafico', params: p }
  },
  mapa: { vista: 'mapa', etiqueta: 'Omisión %' },
  tabla: (filas, c) => (c.pestana === 'mes' ? tablaMes(filas, c) : tablaAnio(filas, c)),
  graficos: (filas, c) => {
    const f = filas[0]
    if (!f) return []
    const anios = Object.keys(f).map((k) => k.match(/^a(\d{4})$/)?.[1]).filter(Boolean).map(Number).sort((a, b) => a - b)
    return [{ opcion: barrasPorAnio({ titulo: `OMISIÓN POR CAPITULOS - ${nombreGrafico(c)}`, eje: 'Omisión %',
      nombre: 'Omisión', anios, valores: anios.map((a) => f[`a${a}`]), sufijo: '%',
      colores: anios.map((_, k) => (k === anios.length - 1 ? '#89A590' : '#D8E1BF')) }) }]
  },
  textos: [{
    descripcion: 'Se considera Omisión Por Capítulos a los hogares que tienen alguna omisión a los capítulos 700, 700a, 602, 602a, 603, 604, 605, 606, 606D, 607, 609, 610, 611, 612 y 1b.',
    formula: 'Omisión Por Capitulo = Hogares con alguna Omisión / Total de Hogares entrevistados * 100',
  }],
}
