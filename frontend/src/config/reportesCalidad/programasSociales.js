// Indicadores de seguimiento a programas sociales — seguimientoProgramasSociales.js del sistema actual.
import { pantallaCalidad } from './indicadorCalidad'

export default pantallaCalidad({
  pantalla: 'programas-sociales',
  titulo: 'INDICADORES DE SEGUIMIENTO A PROGRAMAS SOCIALES',
  archivo: 'INDICADORES-PROGRAMAS-SOCIALES',
  indicadores: [
    { v: 24, t: '1. Porcentaje de hogares que han recibido ayuda alimentaria de algún programa social.', unidad: '%',
      descripcion: 'Permite conocer el número de hogares que recibió por parte del estado ayuda alimentaria de algún programa social.',
      formula: 'Hogares con respuesta (p701$01=1 | p701$02=2 | p701$03=3 | p701$04=4 | p701$05=5 | p701$06=6 | p701$07=7 | p701$08=8 | p701$10=10) / total de hogares * 100' },
    // La pantalla actual no tiene objetivo ni fórmula para este indicador
    { v: 49, t: '2. Porcentaje de hogares que han recibido ayuda de un programa social no alimentario (710).', unidad: '%' },
  ],
})
