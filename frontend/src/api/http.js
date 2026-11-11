import axios from 'axios'

// Cliente HTTP único. Sesión de Django por cookie + token CSRF en cabecera.
const http = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  timeout: 60000,
})

// Si la sesión venció, se avisa a la aplicación para volver al login.
http.interceptors.response.use(
  (r) => r,
  (error) => {
    const esAuth = (error.config?.url ?? '').startsWith('/auth/')
    if (!esAuth && (error.response?.status === 401 || error.response?.status === 403)) {
      window.dispatchEvent(new CustomEvent('api:no-autorizado', { detail: error.response.status }))
    }
    return Promise.reject(error)
  },
)

export function mensajeError(error) {
  const datos = error?.response?.data
  if (!datos) return 'No se pudo conectar con el servidor.'
  if (typeof datos.detail === 'string') return datos.detail
  // Mensajes generales (non_field_errors) se muestran sin el nombre del campo
  return Object.entries(datos)
    .map(([campo, msj]) => (campo === 'non_field_errors' ? '' : `${campo}: `) + [].concat(msj).join(' '))
    .join(' · ')
}

export default http
