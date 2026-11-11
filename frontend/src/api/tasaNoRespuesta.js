import http from './http'

/** API de una pantalla de tasa de no respuesta: tnr-total, tnr-parcial, ... */
export default function apiTnr(indicador) {
  const base = `/cobertura/${indicador}`
  return {
    info: () => http.get(`${base}/`),
    vista: (vista, filtros) => http.get(`${base}/${vista}/`, { params: filtros }),
    excel: (vista, filtros, ambito) =>
      http.get(`${base}/${vista}/`, { params: { ...filtros, ambito, formato: 'xlsx' }, responseType: 'blob' }),
    mapa: () => http.get(`${base}/mapa/`),
  }
}
