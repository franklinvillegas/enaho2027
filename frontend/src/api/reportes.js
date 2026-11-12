import http from './http'

/** Pantallas de cobertura con estructura propia (control de visitas, omisiones, ...). */
export default {
  tabla: (pantalla, vista, params) => http.get(`/cobertura/reportes/${pantalla}/${vista}/`, { params }),
  // Excel de la tabla que ya está en pantalla: el servidor solo arma el archivo
  excel: (tabla) => http.post('/excel/', tabla, { responseType: 'blob' }),
}
