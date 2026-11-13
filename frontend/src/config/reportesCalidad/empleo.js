// Indicadores de seguimiento a empleo y otros — seguimientoEmpleoOtros.js del sistema actual.
import { etnicidad, pet, situacionLaboral } from './especiales'
import { EXCLUSIONES_EMPLEO, pantallaCalidad } from './indicadorCalidad'

const NINI = [
  'Solo estudian: (P306 = 1 | (P310B1 & P310D1 >= 2 años)) & (P501 & P502 & P503 & P5041 & P5042 & P5043 & P5044 & P5045 & P5046 & P5047 & P5048 & P5049 & P50410 & P50411 con código 2 o Null)',
  'Solo trabajan: (P306=2 & P310B1=2) & (P501 | P502 | P503 | (P5041 | P5042  P5043 | P5044 | P5045 | P5046 | P5047 | P5048 | P5049 | P50410 | P50411) con código 1)',
  'Estudian y trabajan: (P306 = 1 | (P310B1 & P310D1 >= 2 años)) & (P501 | P502 | P503 | (P5041 | P5042  P5043 | P5044 | P5045 | P5046 | P5047 | P5048 | P5049 | P50410 | P50411) con código 1)',
  'Ni estudian ni trabajan: (P306=2 & P310B1=2) & (P310B1 & P310D1 >= 2 años)) & (P501 & P502 & P503 & P5041 & P5042 & P5043 & P5044 & P5045 & P5046 & P5047 & P5048 & P5049 & P50410 & P50411 con código 2 o Null)',
]

export default pantallaCalidad({
  pantalla: 'empleo',
  titulo: 'INDICADORES DE EMPLEO',
  archivo: 'INDICADORES-EMPLEO',
  exclusiones: EXCLUSIONES_EMPLEO,
  indicadores: [
    { v: 37, t: '1. Total de la población en edad de trabajar (PET).', unidad: '',
      descripcion: 'Permite conocer las personas aptas para ejercer funciones productivas en la economía, la que es representada por las personas residentes de 14 a más años de edad.',
      formula: '(Población total >= 14 / Población total) * 100' },
    { v: 38, t: '2. Población económicamente Activa (PEA).', unidad: '',
      descripcion: 'Permite conocer la distribución de las personas en edad de trabajar que contribuyen y que están disponibles para contribuir en la producción de bienes y servicios.',
      formula: '((Ocupados + desocupados activos) / Población total >= 14 años) * 100' },
    { v: 40, t: '3. PEA según niveles de empleo - ocupados.', unidad: '',
      descripcion: 'Permite conocer la distribución de las personas que contribuyen a la producción de bienes y servicios.',
      formula: '((Ocupados) / (Población total >= 14 años)) * 100' },
    { v: 41, t: '4. PEA según niveles de empleo - desempleo abierto.', unidad: '',
      descripcion: 'Permite conocer la distribución de las personas que, aunque no contribuyen, están disponibles para contribuir en la producción de bienes y servicios.',
      formula: '(Desocupados activo / Población total >= 14 años) * 100' },
    { v: 39, t: '5. Población económicamente inactiva (NO PEA).', unidad: '',
      descripcion: 'Permite conocer la distribución de las personas en edad de trabajar que no realizan ni buscan alguna actividad económica.',
      formula: '(Desocupados inactivos / (Población total >= 14 años) * 100' },
    { v: 31, t: '6. Situación laboral de Personas entre 15 y 24 años de edad.', unidad: '%', especial: situacionLaboral,
      descripcion: 'Permite conocer la situacion de las personas entre los 15 a 24 años de edad que: "solo estudian", "solo trabajan", "estudian y trabajan" y "ni estudian ni trabajan (NINIS)',
      formula: NINI.join('\n') },
    { v: 42, t: '7. PET según condición de actividad (con factor y trimestre móvil).', unidad: '', especial: pet,
      descripcion: 'Conocer la población en edad de trabajar de 14 y más años de edad, con capacidad para desempeñar funciones productivas.',
      formula: 'Población total >= 14 años' },
    { v: 12, t: '8. Porcentaje de personas sin actividad secundaria.', unidad: '%',
      descripcion: 'Se busca conocer según la información recopilada de campo la relación que existe entre la población que no tiene una ocupación secundaria y el total de la población ocupada.',
      formula: 'Total no tienen Act. Secundaria (P514=2 & P515=2(Todas)) / Total Categoría de Ocupación (P507 >= 1) * 100 (PARA CUESTIONARIO COMPLETO)\nTotal no tienen Act. Secundaria (P514=2) / Total Categoría de Ocupación (P507 >= 1) * 100 (PARA CUESTIONARIO REDUCIDO)' },
    { v: 20, t: '9. Porcentaje de casos que no reciben transferencias.', unidad: '%',
      descripcion: 'Permite conocer el número de hogares que no reciben ningún tipo de transferencia en el periodo investigado.',
      formula: 'Total casos que no reciben transferencias corrientes (P556=2 para todas) / Total casos de transferencias corrientes (P556) X 100' },
    { v: 21, t: '10. Porcentaje de casos sin ninguna información de rentas.', unidad: '%',
      descripcion: 'Permite conocer el número de hogares que no recibe ningún tipo de rentas en el periodo investigado, luego si este nivel se encuentra dentro de los valores de aceptación de la respectiva ODEI.',
      formula: 'Total casos que no tienen rentas por propiedades (P557=2 todos los casos) / Total casos de rentas por propiedades (P557 <> de vacío) X 100' },
    { v: 36, t: '11. Etnicidad', unidad: '%', especial: etnicidad,
      descripcion: 'Permite conocer como considera su etnicidad la poblacion según costumbres y antepasados.',
      formula: 'Quechua:P558C = 1, Aymara:P558C = 2, Nativo o Indígena de la Amazonía:P558C = 3,\nNegro/Moreno/Mulato/Zambo/Afroperuano:P558C = 4, Blanco:P558C = 5,\nMestizo:P558C = 6, Otro:P558C = 7 y No Sabe:P558C = 8' },
  ],
})
