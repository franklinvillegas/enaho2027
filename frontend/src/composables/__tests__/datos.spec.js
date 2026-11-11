import { describe, expect, it } from 'vitest'
import { clasificarColumnas, columnasCoordenadas, etiqueta, medidaPrincipal } from '../datos'
import { MENU, menuPara, pantallasDe } from '@/config/menu'

describe('clasificarColumnas', () => {
  it('separa columnas de texto y numéricas', () => {
    const filas = [
      { departamento: 'LIMA', tasa: 12.5, hogares: '320' },
      { departamento: 'CUSCO', tasa: 8, hogares: '150' },
    ]
    expect(clasificarColumnas(['departamento', 'tasa', 'hogares'], filas)).toEqual({
      categoricas: ['departamento'],
      numericas: ['tasa', 'hogares'],
    })
  })
})

describe('medidaPrincipal', () => {
  it('prefiere la tasa', () => {
    expect(medidaPrincipal(['viviendas', 'no_respuesta', 'tasa'])).toBe('tasa')
    expect(medidaPrincipal(['viviendas'])).toBe('viviendas')
  })
})

describe('columnasCoordenadas', () => {
  it('reconoce latitud y longitud', () => {
    expect(columnasCoordenadas(['ubigeo', 'Latitud', 'Longitud'])).toEqual({ lat: 'Latitud', lon: 'Longitud' })
  })
})

describe('etiqueta', () => {
  it('convierte nombres de columna en texto legible', () => {
    expect(etiqueta('tasa_no_respuesta')).toBe('Tasa no respuesta')
    expect(etiqueta('TasaNoRespuesta')).toBe('Tasa no respuesta')
  })
})

describe('menú', () => {
  it('muestra solo los módulos permitidos', () => {
    expect(menuPara(['cobertura']).map((m) => m.modulo)).toEqual(['cobertura'])
  })
  it('agrupa la tasa de no respuesta en un submenú, como el sistema actual', () => {
    const cobertura = MENU.find((m) => m.modulo === 'cobertura')
    const grupo = cobertura.pantallas.find((p) => p.grupo === 'Tasa de no respuesta')
    expect(grupo.pantallas.map((p) => p.slug)).toEqual(['tnr-total', 'tnr-parcial', 'tnr-estrato'])
    expect(pantallasDe(cobertura)).toHaveLength(9)
  })
  it('tiene los 6 módulos del sistema actual', () => {
    expect(MENU).toHaveLength(6)
  })
})

import { colorCasilla, idFila, modeloColumnas, serieMensual } from '../tablaTnr'

describe('tabla TNR', () => {
  it('arma columnas por año desde los datos', () => {
    const m = modeloColumnas(['idMostrar', 'nombreMostrar', 'tnr2012', 'tnr2027', 'tnr2013'])
    expect(m.tipo).toBe('anios')
    expect(m.grupos[0].columnas.map((c) => c.titulo)).toEqual(['2012', '2013', '2027'])
    expect(m.grupos[0].columnas.at(-1).colorear).toBe(true)
  })
  it('arma columnas por mes para cualquier año', () => {
    const cols = ['tnr2027', 'tnr2027_abs', 'enero_2027', 'enero_2027_abs', 'febrero_2027']
    const m = modeloColumnas(cols)
    expect(m.tipo).toBe('meses')
    expect(m.grupos[0].anio).toBe(2027)
    expect(m.grupos[0].columnas.map((c) => c.titulo)).toEqual(['Total', 'Abs', 'Ene', 'Abs', 'Feb'])
  })
  it('usa la escala azul del sistema actual', () => {
    expect(colorCasilla(7).fondo).toBe('#DCF2FD')
    expect(colorCasilla(100).fondo).toBe('#007DC5')
  })
  it('TNR parcial: prefijo tnrp_ y absoluto por año, sin escala azul', () => {
    const m = modeloColumnas(['idMostrar', 'tnrp_2013', 'tnrp_2013_abs', 'tnrp_2026', 'tnrp_2026_abs'],
      { prefijo: 'tnrp_', colorearUltimo: false })
    expect(m.grupos[0].columnas.map((c) => c.titulo)).toEqual(['2013', 'Abs.', '2026', 'Abs.'])
    expect(m.grupos[0].columnas.some((c) => c.colorear)).toBe(false)
  })
  it('meses con su número para resaltar el mes del conglomerado', () => {
    const m = modeloColumnas(['tnrp_2026', 'tnrp_2026_abs', 'marzo_2026', 'marzo_2026_abs'], { prefijo: 'tnrp_' })
    expect(m.grupos[0].columnas.map((c) => c.mes)).toEqual([undefined, undefined, '03', '03'])
  })
  it('N° de fila: idMostrar o id', () => {
    expect(idFila({ idMostrar: 3 })).toBe(3)
    expect(idFila({ id: 5 })).toBe(5)
  })
  it('corta en el gráfico los meses que aún no llegan del año en curso', () => {
    const fila = { enero_2026: 1, febrero_2026: 2, marzo_2026: 0, enero_2025: 4 }
    expect(serieMensual(fila, 2026, new Date(2026, 1, 15))).toEqual([1, 2])
    expect(serieMensual(fila, 2025, new Date(2026, 1, 15))).toHaveLength(12)
  })
})
