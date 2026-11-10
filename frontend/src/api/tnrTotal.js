import http from './http'

const base = '/cobertura/tnr-total'

export default {
  info: () => http.get(`${base}/`),
  vista: (vista, filtros) => http.get(`${base}/${vista}/`, { params: filtros }),
  excel: (vista, filtros, ambito) =>
    http.get(`${base}/${vista}/`, { params: { ...filtros, ambito, formato: 'xlsx' }, responseType: 'blob' }),
  mapa: () => http.get(`${base}/mapa/`),
}
