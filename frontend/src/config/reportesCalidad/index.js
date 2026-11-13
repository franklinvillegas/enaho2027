// Configuración de cada pantalla de indicadores de calidad (vista genérica views/reportes/ReporteView.vue).
import programasSociales from './programasSociales'
import viviendaHogar from './viviendaHogar'

export const CONFIGURACIONES = Object.fromEntries([viviendaHogar, programasSociales].map((c) => [c.pantalla, c]))
