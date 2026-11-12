import http from './http'

/** API de una pantalla de tasa de no respuesta: tnr-total, tnr-parcial, ... */
export default function apiTnr(indicador) {
  const base = `/cobertura/${indicador}`
  return {
    info: () => http.get(`${base}/`),
    vista: (vista, filtros) => http.get(`${base}/${vista}/`, { params: filtros }),
    // Excel de las filas que la pantalla ya tiene: el servidor solo arma el archivo,
    // no vuelve a consultar la base
    excel: (vista, filtros, filas, titulo) =>
      http.post(`${base}/${vista}/excel/`, { filtros, filas, titulo }, { responseType: 'blob' }),
    mapa: () => http.get(`${base}/mapa/`),
  }
}
