import http from './http'

/** Reportes con la vista genérica (cobertura: control de visitas, omisiones...; calidad). */
export default {
  tabla: (modulo, pantalla, vista, params) => http.get(`/${modulo}/reportes/${pantalla}/${vista}/`, { params }),
  // Excel de la tabla que ya está en pantalla: el servidor solo arma el archivo
  excel: (tabla) => http.post('/excel/', tabla, { responseType: 'blob' }),
}
