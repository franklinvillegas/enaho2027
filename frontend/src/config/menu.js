// Menú del sistema: los mismos 6 módulos y pantallas activas del monitoreo actual
// (ver pestaña "Catálogo de pantallas" del documento de reingeniería).
//
// - `modulo` coincide con el código del backend (apps/comun/constantes.py → Modulo).
// - Las pantallas con `indicador` ya están migradas (usan la API nueva).
// - Las demás muestran "En construcción" hasta que se migren.
// - Un elemento con `grupo` es un submenú (como en el sistema actual, p. ej. "Tasa de no
//   respuesta" dentro de cobertura); sus pantallas van en su propio `pantallas`.

export const MENU = [
  {
    modulo: 'operacion_campo',
    titulo: 'Operación de campo',
    icono: 'mdi-map-marker-path',
    pantallas: [
      { slug: 'programacion', titulo: 'Programación del trabajo de campo' },
      { slug: 'banco-preguntas', titulo: 'Banco de preguntas y respuestas' },
      { slug: 'programado-ejecutado', titulo: 'Avance programado vs. ejecutado' },
      { slug: 'plan-recorrido', titulo: 'Plan de recorrido' },
      { slug: 'georreferenciacion', titulo: 'Georreferenciación de viviendas' },
      { slug: 'delimitacion-conglomerados', titulo: 'Delimitación de conglomerados' },
      { slug: 'georreferenciacion-anio', titulo: 'Georreferenciación por año (panel)' },
      { slug: 'georreferenciacion-visitas', titulo: 'Georreferenciación por visitas' },
      { slug: 'personal-activo', titulo: 'Localización del personal activo' },
      { slug: 'personal-campo', titulo: 'Localización del personal de campo' },
      { slug: 'permanencia', titulo: 'Permanencia en conglomerados' },
    ],
  },
  {
    modulo: 'reportes_campo',
    titulo: 'Reportes para el personal de campo',
    icono: 'mdi-clipboard-text-outline',
    pantallas: [
      { slug: 'hogares-por-recuperar', titulo: 'Hogares por recuperar con y sin TNR' },
      { slug: 'insuficiencia-informacion', titulo: 'Hogares con insuficiencia de información' },
      { slug: 'verificacion', titulo: 'Indicadores de verificación' },
      { slug: 'viviendas-panel', titulo: 'Seguimiento a viviendas panel' },
      { slug: 'supervision', titulo: 'Reportes de supervisión' },
    ],
  },
  {
    modulo: 'cobertura',
    titulo: 'Indicadores de cobertura',
    icono: 'mdi-chart-bar',
    pantallas: [
      {
        grupo: 'Tasa de no respuesta',
        pantallas: [
          { slug: 'tnr-total', titulo: 'Tasa de no respuesta total', migrada: true },
          { slug: 'tnr-parcial', titulo: 'Tasa de no respuesta parcial', indicador: 'tnr-parcial' },
          { slug: 'tnr-estrato', titulo: 'Tasa de no respuesta por estrato' },
        ],
      },
      { slug: 'problemas-marco', titulo: 'Tasa de problemas de marco', indicador: 'problemas-marco' },
      {
        slug: 'informacion-indirecta',
        titulo: 'Tasa de información indirecta',
        indicador: 'informacion-indirecta',
      },
      {
        slug: 'control-visitas',
        titulo: 'Control de visitas (número de visitas y tiempo)',
        indicador: 'control-visitas',
      },
      { slug: 'omision-capitulos', titulo: 'Omisión por capítulos' },
      { slug: 'omisiones-gps', titulo: 'Porcentaje de omisiones GPS de las viviendas' },
      { slug: 'tipo-entrevista', titulo: 'Tipo de entrevista', indicador: 'tipo-entrevista' },
    ],
  },
  {
    modulo: 'calidad',
    titulo: 'Indicadores de calidad',
    icono: 'mdi-check-decagram-outline',
    pantallas: [
      { slug: 'vivienda-hogar', titulo: 'Vivienda y hogar' },
      { slug: 'demograficos', titulo: 'Demográficos' },
      { slug: 'consumo-alimentos', titulo: 'Consumo de alimentos' },
      { slug: 'programas-sociales', titulo: 'Programas sociales' },
      { slug: 'educacion', titulo: 'Educación' },
      { slug: 'salud', titulo: 'Salud' },
      { slug: 'empleo', titulo: 'Empleo y otros' },
    ],
  },
  {
    modulo: 'valores_monetarios',
    titulo: 'Valores monetarios',
    icono: 'mdi-cash-multiple',
    pantallas: [
      { slug: 'gasto-total', titulo: 'Gasto total' },
      { slug: 'gastos-grupo', titulo: 'Gastos por grupo' },
      { slug: 'gastos-tipo', titulo: 'Gastos por tipo' },
      { slug: 'ingreso-total', titulo: 'Ingreso total' },
      { slug: 'ingresos-tipo', titulo: 'Ingresos por tipo' },
    ],
  },
  {
    modulo: 'seguimiento_monitor',
    titulo: 'Seguimiento del monitor',
    icono: 'mdi-account-eye-outline',
    pantallas: [
      { slug: 'mensajeria', titulo: 'Sistema de mensajería' },
      { slug: 'uso-monitoreo', titulo: 'Uso del monitoreo' },
      { slug: 'alertas-correo', titulo: 'Registro de alertas de correo' },
      { slug: 'evaluacion-agua', titulo: 'Evaluación del agua' },
      { slug: 'diligenciamiento-p601', titulo: 'Tiempo de diligenciamiento P601' },
      { slug: 'trabajo-campo', titulo: 'Detalles del trabajo de campo' },
      { slug: 'horarios-visitas', titulo: 'Inicio y cierre de visitas según horarios' },
      { slug: 'protocolos', titulo: 'Cumplimiento de protocolos en campo' },
    ],
  },
]

/** Pantallas de un módulo sin los submenús (para rutas, conteos y accesos directos). */
export const pantallasDe = (m) => m.pantallas.flatMap((p) => (p.grupo ? p.pantallas : [p]))

export const rutaModulo = (modulo) => `/${modulo.replaceAll('_', '-')}`

/** Menú visible para un usuario, según los módulos que le devuelve el backend. */
export function menuPara(modulosPermitidos) {
  return MENU.filter((m) => modulosPermitidos.includes(m.modulo))
}
