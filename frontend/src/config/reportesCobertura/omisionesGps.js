// Porcentaje de omisiones GPS — reporte_omisiones.js del sistema actual.
// Filtros ODEI (cambia el nivel), mes y periodo. Niveles: ODEI → encuestador → conglomerado →
// viviendas del conglomerado con sus coordenadas.
import { MES3, MESES_CORTOS, MESES_MAYUS, ambito, barrasPorAnio, enlaceConglomerado, enlaceEncuestador,
  enlaceSede, entero, nav, num } from './comun'

// El procedimiento llama "sep" a setiembre
const CLAVES = MES3.map((m) => (m === 'set' ? 'sep' : m))

const nombreAmbito = (c) => ['ODEI', 'ENCUESTADOR', 'CONGLOMERADO'][c.nivel - 1]

function celdaNombre(f, i, c) {
  if (c.nivel === 1) {
    const cod = String(f.codOdei ?? '')
    // Los códigos de más de dos caracteres (15.1, 15.2...) no tienen detalle
    const enlace = i > 0 && cod.length <= 2 && c.odeiPermitida(cod) ? enlaceSede(cod, f.odei) : null
    return { texto: i === 0 ? f.odei || 'NACIONAL' : f.odei, izquierda: true, enlace }
  }
  if (c.nivel === 2) {
    return { texto: f.nomencue, izquierda: true, enlace: i === 0 ? null : enlaceEncuestador(f.codencue, f.nomencue) }
  }
  return { texto: f.conglome, enlace: i === 0 ? null : enlaceConglomerado(f.conglome) }
}

function tablaResumen(filas, c) {
  return {
    fijas: 1,
    encabezados: [
      [{ texto: nombreAmbito(c), filas: 2 }, { texto: '% DE VIVIENDAS SIN CAPTURA DE PUNTOS GPS', columnas: 13 }],
      [{ texto: 'TOTAL' }, ...MESES_MAYUS.map((m) => ({ texto: m.slice(0, 3) }))],
    ],
    filas: filas.map((f, i) => ({
      total: i === 0,
      celdas: [celdaNombre(f, i, c), { texto: num(f.sinGPS) },
        ...CLAVES.map((m, k) => ({ texto: num(f[m]), resaltado: c.nivel === 3 && Number(f.mes) === k + 1 }))],
    })),
  }
}

function tablaViviendas(filas) {
  const cols = [['conglome', 'CONGLOMERADO'], ['mes', 'MES'], ['dni', 'DNI'], ['encuestador', 'ENCUESTADOR'],
    ['VIVIENDA', 'VIVIENDA'], ['totalHogares', 'TOTAL DE VIVIENDAS'], ['hogar', 'HOGAR'], ['resultado', 'RESULTADO'],
    ['nroReemplazo', 'NRO REEMPLAZO'], ['latitude', 'LATITUD'], ['longitude', 'LONGITUD']]
  return {
    fijas: 0,
    encabezados: [[...cols.map(([, t]) => ({ texto: t })), { texto: 'MAPA' }]],
    filas: filas.map((f) => {
      const lat = Number(f.latitude)
      const lon = Number(f.longitude)
      // -9.9999999 es la marca de "sin GPS" en la base
      const conGps = Number.isFinite(lat) && Number.isFinite(lon) && lat !== -9.9999999 && lon !== -9.9999999
      return {
        celdas: [
          ...cols.map(([k]) => ({ texto: entero(f[k] ?? f[k.toLowerCase()]), izquierda: k === 'encuestador' })),
          conGps ? { texto: 'Ver mapa', url: `https://www.google.com/maps?q=${lat},${lon}` } : { texto: 'Sin GPS' },
        ],
      }
    }),
  }
}

function nombreGrafico(c) {
  if (c.nivel === 1) return 'NACIONAL'
  return c.nivel === 2 ? c.nombreSede || c.sede : `${c.nombreSede || c.sede} - ${c.encuestador || c.usuario}`
}

export default {
  pantalla: 'omisiones-gps',
  archivo: 'OMISIONES-GPS',
  colorEncabezado: '#1565C0',
  usaComboOdei: true,
  filtroSedeNavega: true,
  titulo: (c) => `PORCENTAJE DE OMISIONES GPS - ${ambito(c)}`,
  pestanas: (c) => (c.nivel >= 4
    ? [{ codigo: 'tabular', nombre: 'Resumen tabular' }]
    : [{ codigo: 'grafico', nombre: 'Resumen gráfico' }, { codigo: 'tabular', nombre: 'Resumen tabular' }]),
  filtros: () => ['sede', 'mes', 'periodo'],
  consulta: (c) => {
    const p = { ...nav(c), mes: c.filtros.mes, periodo: c.filtros.periodo }
    return { vista: c.nivel >= 4 ? 'viviendas' : 'resumen', params: p }
  },
  tabla: (filas, c) => (c.nivel >= 4 ? tablaViviendas(filas) : tablaResumen(filas, c)),
  graficos: (filas, c) => {
    const f = filas[0]
    if (!f || c.nivel >= 4) return []
    return [{ opcion: barrasPorAnio({ titulo: `% Viviendas sin captura de puntos GPS - ${nombreGrafico(c)}`,
      eje: '%', nombre: '% sin GPS', anios: MESES_CORTOS, valores: CLAVES.map((m) => f[m]), colores: '#7CB5EC',
      sufijo: '%' }) }]
  },
  textos: [{
    descripcion: 'El Reporte de Omisiones de GPS, nos muestra el porcentaje de viviendas que fueron cargadas al Sistema sin las coordenadas de ubicación satelital (GPS).',
    formula: '% Omisión GPS = Hogares con Omisión (GPS = -9.9999999) / Total de Hogares entrevistados * 100',
  }],
}
