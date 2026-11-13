// Indicadores de consumo de alimentos dentro y fuera del hogar — consumoAlimentosHogar.js del sistema actual.
import { precios } from './especiales'
import { EXCLUSIONES_CALIDAD, pantallaCalidad } from './indicadorCalidad'

export default pantallaCalidad({
  pantalla: 'consumo-alimentos',
  titulo: 'INDICADORES DE CONSUMO DE ALIMENTOS DENTRO Y FUERA DEL HOGAR',
  archivo: 'INDICADORES-CONSUMO-ALIMENTOS',
  conAmbito: false,
  indicadores: [
    { v: 44, t: '1. Promedio de Ítems con SI en el capítulo 601.', unidad: '',
      // Solo este indicador permite excluir con / sin supervisión
      exclusiones: [...EXCLUSIONES_CALIDAD, { v: 4, t: 'Con supervision' }, { v: 5, t: 'Sin supervision' }],
      descripcion: 'Permite conocer el promedio de productos consumidos en el hogar durante el periodo de referencia (capitulo 601)',
      formula: 'Total de p601b = 1 / total de hogares' },
    { v: 22, t: '2. Porcentaje de casos sin consumo de alimentos fuera del hogar.', unidad: '%',
      descripcion: 'Permite conocer el número de hogares que no registra gastos en alimentos fuera del hogar en ninguno de las personas residentes del hogar.',
      formula: 'Total casos sin consumo de alimentos fuera del hogar (P559$01 = 2 AND P559$02 = 2 AND P559$03 = 2 AND P559$04 = 2) / Total consumo de alimentos fuera del hogar (P559$01 IN (1,2,9) AND P559$02 IN (1,2,9) AND P559$03 IN (1,2,9) AND P559$04 IN (1,2,9)) * 100' },
    { v: 46, t: '3. Promedio de gasto en alimentos por persona fuera del hogar (gasto mensual).', unidad: '',
      descripcion: 'Permite conocer el promedio de gasto mensual de alimentos consumidos fuera del hogar por las personas residentes de 14 años a más de edad (desayuno, almuerzo, cena, otros).',
      formula: 'Suma total de [(p559A * p559D) * 4.33] / total de personas de 14 años a más de edad * 100' },
    { v: 43, t: '4. Precios ENAHO Año Actual versus Año Anterior (urbano).', unidad: '', especial: precios },
    { v: 45, t: '5. Consumo total en kilos Cap. 601.', unidad: '',
      descripcion: 'Permite conocer el consumo total en kilos del hogar durante el periodo de referencia (capitulo 601).',
      formula: 'Suma total de [p601b2]' },
    { v: 48, t: '6. Ocurrencias de alimentos consumidos fuera del hogar de personas de 14 a más años de edad.', unidad: '',
      descripcion: 'Permite identificar la cantidad total de alimentos consumidos fuera del hogar por las personas residentes de 14 años a más de edad (desayuno, almuerzo, cena, otros).',
      formula: 'Suma total de [p559n]' },
    { v: 68, t: '7. Promedio del gasto de la canasta 601 del hogar.', unidad: 'Prom.',
      descripcion: 'Permite conocer el promedio de gasto de la canasta del hogar durante el periodo de referencia.',
      formula: 'Suma total de P601C / / total de personas de 14 años a más de edad * 100',
      casos: { titulo: 'GASTOS CANASTA', columnas: [['id', 'N'], ['año', 'Año'], ['odei', 'Cod. ODEI'],
        ['nomodei', 'ODEI'], ['mes', 'Mes'], ['periodo', 'Periodo'], ['conglome', 'Conglomerado'], ['vivienda', 'Vivienda'],
        ['hogar', 'Hogar'], ['result', 'Resultado'], ['codencue', 'DNI'], ['nomencue', 'Personal'],
        ['gastos_canasta', 'Gastos canasta']] } },
  ],
})
