// Configuración de cada reporte de cobertura que usa la vista genérica views/reportes/ReporteView.vue.
import controlVisitas from './controlVisitas'
import omisionCapitulos from './omisionCapitulos'
import omisionesGps from './omisionesGps'
import tipoEntrevista from './tipoEntrevista'

export const CONFIGURACIONES = Object.fromEntries(
  [controlVisitas, omisionCapitulos, omisionesGps, tipoEntrevista].map((c) => [c.pantalla, c]),
)
