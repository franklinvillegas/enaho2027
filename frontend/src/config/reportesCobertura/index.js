// Configuración de cada reporte de cobertura que usa la pantalla genérica ReporteCoberturaView.
import controlVisitas from './controlVisitas'
import omisionCapitulos from './omisionCapitulos'
import omisionesGps from './omisionesGps'
import tipoEntrevista from './tipoEntrevista'

export const CONFIGURACIONES = Object.fromEntries(
  [controlVisitas, omisionCapitulos, omisionesGps, tipoEntrevista].map((c) => [c.pantalla, c]),
)
