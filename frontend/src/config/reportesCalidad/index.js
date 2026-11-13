// Configuración de cada pantalla de indicadores de calidad (vista genérica views/reportes/ReporteView.vue).
import consumoAlimentos from './consumoAlimentos'
import demograficos from './demograficos'
import educacion from './educacion'
import empleo from './empleo'
import programasSociales from './programasSociales'
import salud from './salud'
import viviendaHogar from './viviendaHogar'

export const CONFIGURACIONES = Object.fromEntries([viviendaHogar, demograficos, consumoAlimentos, programasSociales,
  educacion, salud, empleo].map((c) => [c.pantalla, c]))
