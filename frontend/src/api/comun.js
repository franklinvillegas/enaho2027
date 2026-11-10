import http from './http'

export const auth = {
  csrf: () => http.get('/auth/csrf/'),
  login: (usuario, password) => http.post('/auth/login/', { usuario, password }),
  logout: () => http.post('/auth/logout/'),
  yo: () => http.get('/auth/yo/'),
}

export const catalogos = {
  odeis: () => http.get('/catalogos/odeis/'),
}

export const registrarUso = (pantalla, evento) =>
  http.post('/registro-uso/', { pantalla, evento }).catch(() => {})
