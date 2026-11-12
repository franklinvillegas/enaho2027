import http from './http'

const base = '/cobertura/tnr-estrato'

/** API de la pantalla TNR según estrato (pestañas anual, mensual y hogar). */
export default {
  info: () => http.get(`${base}/`),
  tabla: (tabla, params) => http.get(`${base}/${tabla}/`, { params }),
  // Excel de las filas ya cargadas en la pestaña: no vuelve a consultar la base
  excel: (tabla, filtros, filas, titulo) =>
    http.post(`${base}/${tabla}/excel/`, { filtros, filas, titulo }, { responseType: 'blob' }),
}
