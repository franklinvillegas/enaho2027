import http from './http'

const base = '/cobertura/indicadores'

export default {
  indicadores: () => http.get(`${base}/`),
  datos: (codigo, filtros) => http.get(`${base}/${codigo}/`, { params: filtros }),
  mapa: (codigo) => http.get(`${base}/${codigo}/mapa/`),
  excel: (codigo, filtros) =>
    http.get(`${base}/${codigo}/`, { params: { ...filtros, formato: 'xlsx' }, responseType: 'blob' }),
}
