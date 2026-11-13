// Indicadores de vivienda y hogar — viviendaHogar.js del sistema actual.
import { pantallaCalidad } from './indicadorCalidad'

const SERVICIO = 'Si se encuentra por debajo del rango de aceptación se puede tratar de un error de interpretación del (la) encuestador(a), caso contrario se debería analizar donde está ubicada la muestra.'

// "Visualizar casos" de los indicadores de balance del hogar (calidad_viviendaHogar_detalleBalanceHogar)
const COLUMNAS_BALANCE = [
  ['id', 'N'], ['año', 'Año'], ['odei', 'Cod. ODEI'], ['nomodei', 'ODEI'], ['mes', 'Mes'], ['periodo', 'Periodo'],
  ['conglome', 'Conglomerado'], ['vivienda', 'Vivienda'], ['hogar', 'Hogar'], ['result', 'Resultado'],
  ['ingreso_total', 'Ingreso total S/.'], ['ingreso01', 'Ingreso01'], ['ingreso02', 'Ingreso02'],
  ['ingreso03', 'Ingreso03'], ['ingreso04', 'Ingreso04'], ['ingreso05', 'Ingreso05'],
  ['ingreso_trabajo', 'Ingreso por trabajo S/.'], ['alquiler_imputado', 'Alquiler imputado S/.'],
  ['gasto_total', 'Gasto total S/.'], ['gasto01', 'Gasto01'], ['gasto02', 'Gasto02'], ['gasto03', 'Gasto03'],
  ['gasto04', 'Gasto04'], ['gasto05', 'Gasto05'], ['gasto06', 'Gasto06'], ['gasto07', 'Gasto07'],
  ['gasto08', 'Gasto08'], ['gasto_alimentosbebidas', 'Gasto alimentos y bebidas S/.'],
  ['gasto_alimentosdentrohogar', 'Gasto alimentos dentro del hogar 601 S/.'], ['codencue', 'DNI'],
  ['nomencue', 'Personal'], ['balance', 'Balance'],
]

export default pantallaCalidad({
  pantalla: 'vivienda-hogar',
  titulo: 'INDICADORES DE VIVIENDA Y HOGAR',
  archivo: 'INDICADORES-VIVIENDA-HOGAR',
  indicadores: [
    { v: 1, t: '1. Promedio de habitaciones por vivienda.', unidad: '',
      descripcion: 'Mide los posibles errores en el registro del número de habitaciones, en los casos que este sea muy alto (dependiendo donde sea la ubicación de la muestra) o muy bajo (alto nivel de hacinamiento).',
      formula: 'Total de Habitaciones (P104) / Total de Viviendas' },
    { v: 3, t: '2. Porcentaje de viviendas con 2 o mas hogares.', unidad: '%',
      descripcion: 'Indicador a través del cual podremos conocer la posible omisión de hogares secundarios',
      formula: 'Total  Viviendas con 2 o más hogares secundarios (P11B >= 2)  / Total  Viviendas (P11B >= 1) * 100' },
    { v: 16, t: '3. Porcentaje de casos sin información de alquiler imputado.', unidad: '%',
      descripcion: 'Permite conocer el nivel de omisión existente en esta pregunta que es estimada por los informantes.',
      formula: 'Total casos sin información de alquiler imputado (P105A=2:7 & P106=999999) / Total casos alquiler imputado (P105A=2:7) * 100' },
    { v: 4, t: '4. Porcentaje de hogares que tienen conexión de agua.', unidad: '%',
      descripcion: `Permite conocer el número de hogares que cuentan con el servicio de agua potable. ${SERVICIO}`,
      formula: '(P110 = 1:3 / Total de Hogares con resultado 1:2) * 100' },
    { v: 5, t: '5. Porcentaje de hogares que tienen servicio higiénico.', unidad: '%',
      descripcion: 'Permite conocer el número de hogares que tienen servicio higiénico. Este indicador debe ser evaluado según el lugar donde está ubicada la muestra. Si se encuentra por debajo del rango de aceptación se puede tratar de un error de interpretación del (la) encuestador(a).',
      formula: '(P111 = 1:4 / Total de Hogares con resultado 1:2) * 100' },
    { v: 30, t: '6. Porcentaje de hogares que tienen Electricidad.', unidad: '%',
      descripcion: `Permite conocer el número de hogares que tienen Electricidad. ${SERVICIO}`,
      formula: '(P112 = 1 / Total de Hogares con resultado 1:2) * 100' },
    { v: 32, t: '7. Porcentaje de Hogares que tienen Celular.', unidad: '%',
      descripcion: `Permite conocer el número de hogares que tienen celular. ${SERVICIO}`,
      formula: '(P114_2 = 2 / Total de Hogares con resultado 1:2) * 100' },
    { v: 33, t: '8. Porcentaje de Hogares que tienen Tv Cable.', unidad: '%',
      descripcion: `Permite conocer el número de hogares que tienen TV Cable. ${SERVICIO}`,
      formula: '(P114_3 = 3 / Total de Hogares con resultado 1:2) * 100' },
    { v: 34, t: '9. Porcentaje de Hogares que tienen Internet.', unidad: '%',
      descripcion: `Permite conocer el número de hogares que tienen Internet. ${SERVICIO}`,
      formula: '(p114_4=4 y (p114B= 1 o 2 o  (p114B_1=1 o p114B_2=2)) / total de hogares con resultado 1:2) * 100' },
    { v: 35, t: '10. Porcentaje de Hogares que tienen Teléfono.', unidad: '%',
      descripcion: `Permite conocer el número de hogares que tienen Teléfono. ${SERVICIO}`,
      formula: '(P114_1 = 1 / Total de Hogares con resultado 1:2) * 100' },
    { v: 65, t: '11. Porcentaje de hogares con déficit en el balance del hogar.', unidad: '%',
      descripcion: 'Medir el porcentaje de hogares con déficit en el balance (el gasto supera al ingreso), considerando solo a los hogares que superan el -20% de déficit. De tal forma que se pueda verificar los casos observados y que estos no superen las cifras de años anteriores.',
      formula: 'Total de (ingresos – gastos) / Total de ingresos * 100, menores al 20%',
      casos: { titulo: 'BALANCE DEL HOGAR - DÉFICIT', columnas: COLUMNAS_BALANCE } },
    { v: 66, t: '12. Porcentaje de hogares con superávit en el balance del hogar.', unidad: '%',
      descripcion: 'Medir el porcentaje de hogares con superávit en el balance (el ingreso supera al gasto), considerando solo a los hogares que superan el 20% de superávit. De tal forma que se pueda verificar los casos observados y que estos no superen las cifras de años anteriores.',
      formula: 'Total de (ingresos – gastos) / Total de ingresos * 100, mayores al 20%.',
      casos: { titulo: 'BALANCE DEL HOGAR - SUPERÁVIT', columnas: COLUMNAS_BALANCE } },
  ],
})
