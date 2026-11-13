// Indicadores de seguimiento a salud — seguimientoSalud.js del sistema actual.
import { EXCLUSIONES_SEGUIMIENTO, pantallaCalidad } from './indicadorCalidad'

const ACCESO = 'Permite evaluar las dificultades que tiene la población para acceder a los servicios de salud.'
const RAZONES = ['No tuvo dinero', 'Se encuentra lejos', 'Demoran mucho en atender', 'No confía en los médicos',
  'No era grave / no fue necesario', 'Prefiere curarse con remedios caseros', 'No tiene seguro',
  'Se auto receto o repitió receta anterior', 'Falta de tiempo', 'Por el maltrato del personal de salud', 'Otro']

export default pantallaCalidad({
  pantalla: 'salud',
  titulo: 'INDICADORES DE SEGUIMIENTO A SALUD',
  archivo: 'INDICADORES-SALUD',
  exclusiones: EXCLUSIONES_SEGUIMIENTO,
  indicadores: [
    { v: 11, t: '1. Porcentaje de personas con enfermedad, síntoma, recaída o accidente (P402).', unidad: '%',
      descripcion: 'Permite conocer qué porcentaje de la muestra presenta alguna enfermedad en el periodo investigado y si estos se encuentran dentro del rango de aceptación, caso contrario ameritarán su verificación.',
      formula: 'Total de Pers. que Presentan Enferm. (P402=1 o 2 o 3 o 4 o 6 & codinform>0 ) / Total de Personas Residentes * 100' },
    { v: 56, t: '2. Porcentaje de personas con enfermedades crónicas (P401F).', unidad: '',
      descripcion: 'Se busca conocer si los miembros del hogar padecen de alguna enfermedad crónica o malestar permanente, y que llevan un tratamiento médico de manera continua acerca de esta enfermedad, cuanto representan del total de personas registradas.',
      formula: 'P401F = 1 / Total casos y residentes * 100' },
    { v: 57, t: '3. Razones de no asistencia a un centro de salud.', unidad: '',
      descripcion: ACCESO, formula: 'P409 = (1 o 2 o 3 … 11) / Total casos y residentes * 100',
      // Combo "RAZONES:": "Seleccione" = todas las razones (57); cada razón tiene su código (69..79)
      subindicadores: [{ v: 57, t: 'Seleccione' }, ...RAZONES.map((r, k) => ({ v: 69 + k, t: `${k + 1}. ${r}`,
        descripcion: `${ACCESO} Caso: ${r}.`, formula: `P409 = ${k + 1} / Total casos y residentes * 100` }))] },
    { v: 58, t: '4. Población menor de 3 años de edad que han realizado control de crecimiento del niño sano.', unidad: '',
      descripcion: 'Permite determinar si durante el período de referencia los hogares recibieron o realizaron consultas de salud correspondientes a control de crecimiento del niño sano/control integral del niño y/o programas de vacunas de promoción de prácticas saludables.',
      formula: '(P208A < 3 y p4131=1) / (P208A < 3) Total casos y residentes * 100' },
    { v: 59, t: '5. Porcentaje de la población con seguro de salud.', unidad: '',
      descripcion: 'Permite conocer la cobertura de la seguridad social, es decir, la cantidad de personas que se encuentran cubiertos por algún sistema de prestaciones de salud.',
      formula: 'P419= (1 o 2 o 3…8) / Total casos y residentes * 100' },
  ],
})
