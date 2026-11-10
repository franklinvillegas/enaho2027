import { describe, expect, it } from 'vitest'
import { clasificarColumnas, columnasCoordenadas, etiqueta, medidaPrincipal } from '../datos'
import { MENU, menuPara } from '@/config/menu'

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
  it('tiene los 6 módulos del sistema actual', () => {
    expect(MENU).toHaveLength(6)
  })
})
