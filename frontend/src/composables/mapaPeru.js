// Mapa de calor del Perú por departamento (sin servicios externos: límites INEI-2007
// servidos por el propio sistema en /geo/peru_departamentos.geojson).
import { registerMap } from 'echarts/core'

let registrado = null

/** Registra el mapa 'peru' en ECharts una sola vez. */
export function registrarMapaPeru() {
  registrado ??= fetch('/geo/peru_departamentos.geojson')
    .then((r) => r.json())
    .then((geo) => {
      geo.features.forEach((f) => (f.properties.name = f.properties.NOMBDEP))
      registerMap('peru', geo)
    })
  return registrado
}

export const normalizar = (t) => String(t ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().trim()

/** filas: [{ departamento, indicador }] tal como las devuelven los procedimientos *_map. */
export function opcionesMapaCalor(filas, etiqueta) {
  const datos = filas.map((d) => ({ name: normalizar(d.departamento), value: Number(d.indicador) }))
  const valores = datos.map((d) => d.value)
  const min = valores.length ? Math.min(...valores) : 0
  const max = valores.length ? Math.max(...valores) : 1
  return {
    tooltip: { formatter: (p) => `<b>${p.name}</b><br>${etiqueta}: <b>${p.value ?? '-'}</b>` },
    visualMap: { min, max, left: 20, bottom: 20, orient: 'horizontal', calculable: false,
      text: [String(max), String(min)], inRange: { color: ['#EFE8DF', '#3A95F7'] } },
    series: [{ type: 'map', map: 'peru', roam: false, data: datos, aspectScale: 1,
      layoutCenter: ['50%', '50%'], layoutSize: '98%',
      itemStyle: { borderColor: '#FFFFFF', areaColor: '#F4F4F4' },
      emphasis: { label: { show: false }, itemStyle: { areaColor: '#1565C0' } } }],
  }
}
