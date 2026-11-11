import http from './http'

const base = '/cobertura/tnr-estrato'

/** API de la pantalla TNR según estrato (pestañas anual, mensual y hogar). */
export default {
  info: () => http.get(`${base}/`),
  tabla: (tabla, params) => http.get(`${base}/${tabla}/`, { params }),
  excel: (tabla, params, detalle) =>
    http.get(`${base}/${tabla}/`, { params: { ...params, detalle, formato: 'xlsx' }, responseType: 'blob' }),
}
