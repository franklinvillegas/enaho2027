// Indicadores de calidad con estructura propia: reemplazan partes del esquema común
// (indicadorCalidad.js). Cada uno replica la pantalla actual:
//   piramide            demograficos.js           9. Pirámide de edad
//   precios             consumoAlimentosHogar.js  4. Precios ENAHO año actual vs anterior
//   asistenciaEscolar   seguimientoEducacion.js   3. Tasa de asistencia escolar (con dominio)
//   situacionLaboral    seguimientoEmpleoOtros.js 6. Situación laboral de 15 a 24 años
//   pet                 seguimientoEmpleoOtros.js 7. PET según condición de actividad
//   etnicidad           seguimientoEmpleoOtros.js 11. Etnicidad
import { FILTROS_RANGO, MESES, MESES_CORTOS, MESES_MAYUS, aniosEn, barrasPorAnio, enlaceEncuestador, enlaceSede,
  entero, esSubsede, hastaMesActual, lineasPorMes, nav, num, rango } from '../reportesCobertura/comun'
import { COLOR_SUFIJO, SUFIJOS, anioDe, celdasFijas, esTotal, nombreColumna, subtituloFiltros, tablaPorMes,
  tituloLargo } from './indicadorCalidad'

const SOLO_TABULAR = [{ codigo: 'tabular', nombre: 'Resumen tabular' }]
const GRAFICO_Y_TABULAR = [{ codigo: 'grafico', nombre: 'Resumen gráfico' }, ...SOLO_TABULAR]
const PALETA = ['#7CB5EC', '#434348', '#90ED7D', '#F7A35C', '#8085E9', '#F15C80', '#E4D354', '#2B908F']
const n = (v) => (v == null || v === '' ? null : Number(v))

/** Columnas agrupadas: una serie por grupo, categorías en el eje X. */
function barrasAgrupadas({ titulo, subtitulo, eje, categorias, series, sufijo = '', anchoTitulo = 820 }) {
  return {
    title: { text: titulo, subtext: subtitulo, left: 'center', textStyle: { fontSize: 14, width: anchoTitulo, overflow: 'break' } },
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v == null ? '-' : `${Number(v).toFixed(1)}${sufijo}`) },
    toolbox: { right: 10, feature: { saveAsImage: { title: 'Descargar' } } },
    legend: { bottom: 0 },
    grid: { left: 60, right: 20, top: subtitulo ? 90 : 70, bottom: 60 },
    xAxis: { type: 'category', data: categorias.map(String) },
    yAxis: { type: 'value', name: eje, nameLocation: 'middle', nameGap: 42 },
    series: series.map((s, k) => ({ name: s.nombre, type: 'bar', color: s.color ?? PALETA[k % PALETA.length],
      data: s.datos.map(n),
      label: { show: true, position: 'top', fontSize: 9, formatter: (p) => (p.value == null ? '' : Number(p.value).toFixed(1)) } })),
  }
}

function torta({ titulo, datos }) {
  return {
    title: { text: titulo, left: 'center', textStyle: { fontSize: 14, width: 420, overflow: 'break' } },
    tooltip: { trigger: 'item', valueFormatter: (v) => `${Number(v).toFixed(1)} %` },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: '58%', center: ['50%', '52%'],
      data: datos.map((d, k) => ({ name: d.nombre, value: n(d.valor), itemStyle: { color: PALETA[k] } })),
      label: { formatter: (p) => `${p.name}: ${Number(p.value).toFixed(1)} %` } }],
  }
}

// ---------------------------------------------------------------------------------------
// 9. Pirámide de edad (demográficos): el año en curso y los dos anteriores
// ---------------------------------------------------------------------------------------
const DEPARTAMENTOS = ['NACIONAL', 'AMAZONAS', 'ANCASH', 'APURIMAC', 'AREQUIPA', 'AYACUCHO', 'CAJAMARCA', 'CALLAO',
  'CUSCO', 'HUANCAVELICA', 'HUANUCO', 'ICA', 'JUNIN', 'LA LIBERTAD', 'LAMBAYEQUE', 'LIMA', 'LORETO',
  'MADRE DE DIOS', 'MOQUEGUA', 'PASCO', 'PIURA', 'PUNO', 'SAN MARTIN', 'TACNA', 'TUMBES', 'UCAYALI']
  .map((t, k) => ({ v: String(k).padStart(2, '0'), t }))

const porAnio = (filas) => {
  const anios = [...new Set(filas.map((f) => f.anio_piramide))].sort((a, b) => b - a)
  return anios.map((a) => ({ anio: a, filas: filas.filter((f) => f.anio_piramide === a) }))
}

export const piramide = {
  vistas: () => [],
  pestanas: () => GRAFICO_Y_TABULAR,
  titulo: (c, { titulo }) => titulo,
  filtros: () => [{ campo: 'departamento', etiqueta: 'Departamento:', opciones: DEPARTAMENTOS }, ...FILTROS_RANGO, 'excluir'],
  consulta: (c) => ({ vista: 'piramide', params: { indicador: 100, departamento: c.filtros.departamento,
    ...rango(c), excluir: c.filtros.excluir } }),
  graficos: (filas, c) => {
    const lugar = DEPARTAMENTOS.find((d) => d.v === c.filtros.departamento)?.t ?? ''
    return porAnio(filas).map(({ anio, filas: fa }) => {
      // La fila del total no va en el dibujo
      const datos = fa.filter((f) => !/total/i.test(String(f.nom_rango)))
      const serie = (nombre, clave, signo, color, pila) => ({
        name: nombre, type: 'bar', stack: pila, color, barGap: '-100%', barWidth: '70%',
        z: pila === 'proyeccion' ? 1 : 2, data: datos.map((f) => signo * Number(f[clave])),
      })
      return { ancho: 'tercio', alto: 560, opcion: {
        title: { text: `Pirámide de edad ${anio} - ${lugar}`, subtext: subtituloFiltros(c), left: 'center',
          textStyle: { fontSize: 14 }, subtextStyle: { width: 360, overflow: 'break' } },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
          valueFormatter: (v) => `${Math.abs(Number(v)).toFixed(1)}%` },
        legend: { bottom: 0 },
        grid: { left: 70, right: 20, top: 90, bottom: 70 },
        xAxis: { type: 'value', axisLabel: { formatter: (v) => `${Math.abs(v)}%` } },
        yAxis: { type: 'category', data: datos.map((f) => f.nom_rango) },
        series: [
          serie('Varones Proyec.', 'porcVaronesProyec', -1, '#9DB8F9', 'proyeccion'),
          serie('Mujeres Proyec.', 'porcMujeresProyec', 1, '#FDBEBE', 'proyeccion'),
          serie('Varones', 'porcVarones', -1, '#5889FE', 'encuesta'),
          serie('Mujeres', 'porcMujeres', 1, '#FF8787', 'encuesta'),
        ],
      } }
    })
  },
  tabla: (filas) => {
    const grupos = porAnio(filas)
    const base = grupos[0]?.filas ?? []
    return {
      fijas: 1,
      encabezados: [
        [{ texto: 'RANGO DE EDAD', filas: 3 }, ...grupos.map((g) => ({ texto: g.anio, columnas: 6 }))],
        grupos.flatMap(() => [{ texto: 'VARONES', columnas: 3 }, { texto: 'MUJERES', columnas: 3 }]),
        grupos.flatMap(() => ['Cant.', 'Porc.', 'Porc. Proyección', 'Cant.', 'Porc.', 'Porc. Proyección']
          .map((t) => ({ texto: t }))),
      ],
      filas: base.map((f, i) => ({
        total: i === 0,
        celdas: [{ texto: f.nom_rango, izquierda: true }, ...grupos.flatMap((g) => {
          const x = g.filas[i] ?? {}
          return [entero(x.varones), num(x.porcVarones), num(x.porcVaronesProyec),
            entero(x.mujeres), num(x.porcMujeres), num(x.porcMujeresProyec)].map((t) => ({ texto: t }))
        })],
      })),
    }
  },
}

// ---------------------------------------------------------------------------------------
// 4. Precios ENAHO año actual vs año anterior (consumo de alimentos)
//    Al hacer clic en la ODEI o en el código del producto se ve el detalle (en la pantalla
//    actual se abría en una ventana; aquí es un nivel más, con "Atrás" y Excel).
// ---------------------------------------------------------------------------------------
const OPC_MES = MESES_MAYUS.map((t, k) => ({ v: k + 1, t }))
const DETALLES = {
  provincias: {
    titulo: (o) => `REPORTE DE PRECIOS - PROVINCIAS DE ${o}`,
    columnas: [['id', 'N°'], ['anio', 'AÑO'], ['mes', 'MES'], ['nomodei', 'ODEI'], ['provincia', 'PROVINCIA'],
      ['produc', 'COD. PROD.'], ['descripcion', 'DESCRIPCIÓN'], ['precio_enaho', 'PRECIO ENAHO']],
  },
  lista: {
    titulo: (o) => `REPORTE DIFERENCIA DE PRECIOS DE ${o}`,
    columnas: [['id', 'N°'], ['año', 'AÑO'], ['mes', 'MES'], ['nomodei', 'ODEI'], ['estrato', 'ESTRATO'],
      ['conglome', 'CONGLOMERADO'], ['vivienda', 'VIVIENDA'], ['hogar', 'HOGAR'], ['produc61', 'COD. PROD.'],
      ['descrip', 'DESCRIPCIÓN'], ['frec_des', 'FRECUENCIA'], ['lugar_compra', 'LUGAR'], ['p601a', 'P601A'],
      ['cantidad', 'CANT.'], ['unid_med_des', 'UNID. MEDIDA'], ['monto_compra', 'MONTO'], ['precio', 'PRECIO x KG.']],
  },
}
const detalleDe = (c) => (DETALLES[c.query?.detalle] && /^\d{6}$/.test(c.query?.producto ?? '') ? c.query.detalle : null)

export const precios = {
  vistas: () => [],
  titulo: (c, { titulo }) => titulo,
  pestanas: (c) => (detalleDe(c) ? SOLO_TABULAR : GRAFICO_Y_TABULAR),
  filtros: () => [
    { campo: 'anio', etiqueta: 'AÑO:', opciones: Array.from({ length: new Date().getFullYear() - 2015 }, (_, k) => ({ v: 2016 + k, t: String(2016 + k) })) },
    { campo: 'odei', etiqueta: 'ODEI:', opciones: 'odeis' },
    { campo: 'mes_precios', etiqueta: 'MES:', opciones: OPC_MES },
  ],
  consulta: (c) => {
    const d = detalleDe(c)
    const params = { indicador: 43, anio: c.filtros.anio, odei: String(c.filtros.odei), mes: c.filtros.mes_precios }
    return d ? { vista: `precios-${d}`, params: { ...params, producto: c.query.producto } } : { vista: 'precios', params }
  },
  migas: (c) => {
    const d = detalleDe(c)
    if (!d) return null
    return [{ texto: 'PRECIOS', ir: { detalle: null, producto: null } },
      { texto: `${d === 'provincias' ? 'PROVINCIAS' : 'HOGARES'} - PRODUCTO ${c.query.producto}` }]
  },
  graficos: (filas, c) => {
    if (detalleDe(c)) return []
    const anio = Number(c.filtros.anio)
    // Como la pantalla actual: los primeros 20 productos, un gráfico por producto
    return filas.slice(0, 20).map((f) => ({ ancho: 'tercio', alto: 330, opcion: {
      title: { text: `${f.descrip} - ${f.nom_odei}`, left: 'center', textStyle: { fontSize: 12, width: 300, overflow: 'break' } },
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 10, top: 60, bottom: 30 },
      xAxis: { type: 'category', data: [`PRECIO ${anio}`, `PRECIO ${anio - 1}`] },
      yAxis: { type: 'value', name: 'Precio en soles', nameLocation: 'middle', nameGap: 36 },
      series: [{ type: 'bar', barWidth: '50%', data: [
        { value: n(f.precio_enaho), itemStyle: { color: '#7CB5EC' } },
        { value: n(f.precio_anio_anterior), itemStyle: { color: '#434348' } }],
      label: { show: true, position: 'top', fontSize: 10 } }],
    } }))
  },
  tabla: (filas, c) => {
    const d = detalleDe(c)
    const odei = filas[0]?.nomodei ?? filas[0]?.nom_odei ?? ''
    if (d) {
      const cols = DETALLES[d].columnas
      return { fijas: 0,
        encabezados: [[{ texto: DETALLES[d].titulo(odei), columnas: cols.length }], cols.map(([, t]) => ({ texto: t }))],
        filas: filas.map((f) => ({ celdas: cols.map(([k]) => ({ texto: f[k] ?? '', izquierda: k.startsWith('descrip') })) })) }
    }
    return {
      fijas: 0,
      encabezados: [[{ texto: 'DIFERENCIA PRECIOS ENAHO AÑO ACTUAL vs AÑO ANTERIOR', columnas: 9 }],
        ['N°', 'AÑO', 'MES', 'ODEI', 'CODIGO\nPRODUCTO', 'DESCRIPCIÓN', 'PRECIO AÑO ACTUAL', 'PRECIO AÑO ANTERIOR', 'DIFERENCIA']
          .map((t) => ({ texto: t }))],
      filas: filas.map((f) => ({ celdas: [
        { texto: f.id }, { texto: f['año'] }, { texto: f.mes },
        { texto: f.nom_odei, enlace: { detalle: 'provincias', producto: String(f.cod_prod) } },
        { texto: f.cod_prod, enlace: { detalle: 'lista', producto: String(f.cod_prod) } },
        { texto: f.descrip, izquierda: true },
        { texto: num(f.precio_enaho) }, { texto: num(f.precio_anio_anterior) }, { texto: num(f.diferencia) },
      ] })),
    }
  },
}

// ---------------------------------------------------------------------------------------
// 3. Tasa de asistencia escolar (educación), con combo de dominio
// ---------------------------------------------------------------------------------------
const DOMINIOS = [{ v: 0, t: 'SELECCIONAR' }, { v: 1, t: 'SEGÚN SEXO' }, { v: 2, t: 'SEGÚN GRUPO DE EDAD' },
  { v: 3, t: 'SEGÚN CENTRO DE ESTUDIOS' }]
// Subcolumnas de cada dominio: sufijo de la columna por año y número por mes
const CATEGORIAS = {
  1: [['Hombre', '_h'], ['Mujer', '_m']],
  2: [['E. Inicial(3-5)', '_ini'], ['E. Prim(6-11)', '_pri'], ['E. Sec(12-16)', '_sec']],
  3: [['Estatal', '_e'], ['No est.', '_ne']],
}
const SIN_DETALLE = ['NACIONAL', 'LIMA PROV.', 'PROV. CONST. CALLAO', 'REGION LIMA']
const SECCIONES = ['AMBITO GEOGRAFICO', 'DOMINIOS', 'DEPARTAMENTOS']
const dominioDe = (c) => (c.vista === 'departamentos' ? 0 : Number(c.query?.dominio ?? 0) || 0)
const totalAE = (f) => Number(f.id) === 0 || SECCIONES.includes(f.nombreMostrar)

function nombreAE(f, c) {
  if (c.vista === 'departamentos') return { texto: f.nombreMostrar, izquierda: true }
  if (c.nivel === 1) {
    const enlace = !SIN_DETALLE.includes(f.nombreMostrar) && !totalAE(f) && !esSubsede(f.idMostrar)
      && c.odeiPermitida(f.idMostrar) ? enlaceSede(f.idMostrar, f.nombreMostrar) : null
    return { texto: f.nombreMostrar, izquierda: true, enlace }
  }
  if (c.nivel === 2) {
    return { texto: f.encuestador ?? '', izquierda: true,
      enlace: Number(f.id) === 0 ? null : enlaceEncuestador(f.usuario, f.encuestador) }
  }
  return { texto: f.conglomerado, izquierda: true }
}

// Columnas por mes: [Y-2, Y-1, Y] (en el detalle de un encuestador solo Y)
function sufijosAE(c, d) {
  const anios = c.nivel >= 3 ? [0] : [2, 1, 0]
  return anios.map((atras) => ({
    anio: c.anio - atras,
    claves: d === 0
      ? [atras === 2 ? 'Anterior2' : atras === 1 ? 'Anterior' : 'Actual']
      : CATEGORIAS[d].map((_, k) => (atras === 2 ? `Anterior${k + 1}b` : atras === 1 ? `Anterior${k + 1}` : `Actual${k + 1}`)),
  }))
}

export const asistenciaEscolar = {
  exclusiones: [{ v: 0, t: 'Sin exclusiones' }, { v: 1, t: 'Excluir no panel' }, { v: 2, t: 'Excluir panel' }],
  selectores: (c) => (c.vista === 'departamentos' ? [] : [{ clave: 'dominio', etiqueta: 'DOMINIO:', opciones: DOMINIOS }]),
  consulta: (c) => ({ vista: c.vista, params: { indicador: 91, ...nav(c), dominio: dominioDe(c), ...rango(c),
    excluir: c.filtros.excluir } }),
  tabla: (filas, c) => {
    const d = dominioDe(c)
    const cats = d ? CATEGORIAS[d] : [['', '']]
    const ambito = c.vista === 'departamentos' ? 'DOMINIOS DE ESTUDIO' : ['ODEI', 'ENCUESTADOR', 'CONGLOMERADO'][c.nivel - 1]
    const conSub = d !== 0
    if (c.vista !== 'odei-mes') {
      const anios = aniosEn(filas, /^indicador(\d{4})/)
      const dec = c.vista === 'departamentos' ? 2 : 1
      return {
        fijas: 1,
        encabezados: [
          [{ texto: ambito, filas: conSub ? 2 : 1 }, ...anios.map((a) => ({ texto: a, columnas: cats.length }))],
          ...(conSub ? [anios.flatMap(() => cats.map(([t]) => ({ texto: t })))] : []),
        ],
        filas: filas.map((f) => ({ total: totalAE(f),
          celdas: [nombreAE(f, c), ...anios.flatMap((a) => cats.map(([, s]) => ({ texto: num(f[`indicador${a}${s}`], dec) })))] })),
      }
    }
    const grupos = sufijosAE(c, d)
    const rojo = c.nivel >= 3
    const yy = (a) => String(a).slice(2)
    return {
      fijas: 1,
      encabezados: [
        [{ texto: ambito, filas: conSub ? 2 : 1 }, ...grupos.flatMap((g) => ['TOTAL', ...MESES_CORTOS.map((m) => m.toUpperCase())]
          .map((m) => ({ texto: `${m}-${yy(g.anio)}`, columnas: cats.length })))],
        ...(conSub ? [grupos.flatMap(() => Array.from({ length: 13 }, () => cats.map(([t]) => ({ texto: t }))).flat())] : []),
      ],
      filas: filas.map((f) => ({ total: totalAE(f), celdas: [nombreAE(f, c), ...grupos.flatMap((g) =>
        ['indicador', ...MESES].flatMap((m) => g.claves.map((k) => {
          const v = f[`${m}${k}`]
          // En el detalle de un encuestador, los meses con casos van en rojo
          return { texto: num(v), resaltado: rojo && Number(v) > 0 }
        })))] })),
    }
  },
  graficos: (filas, c) => {
    const f = filas.find((x) => Number(x.id) === 0) ?? filas[0]
    if (!f) return []
    const d = dominioDe(c)
    const subtitulo = d ? DOMINIOS[d].t : (c.vista === 'departamentos' ? 'SEGÚN DEPARTAMENTO' : '')
    const titulo = 'TASA DE ASISTENCIA ESCOLAR'
    if (c.vista !== 'odei-mes') {
      const anios = aniosEn(filas, /^indicador(\d{4})/)
      if (!d) {
        return [{ alto: 460, opcion: barrasPorAnio({ titulo, subtitulo, eje: 'Tasa', nombre: 'Tasa', anios,
          valores: anios.map((a) => f[`indicador${a}`]), colores: '#7CB5EC' }) }]
      }
      return [{ alto: 460, opcion: barrasAgrupadas({ titulo, subtitulo, eje: 'Tasa', categorias: anios,
        series: CATEGORIAS[d].map(([nombre, s]) => ({ nombre, datos: anios.map((a) => f[`indicador${a}${s}`]) })) }) }]
    }
    if (!d) {
      return [{ alto: 460, opcion: lineasPorMes({ titulo, subtitulo, eje: 'Tasa',
        series: SUFIJOS.filter((s) => c.nivel < 3 || s === 'Actual').map((s) => ({ nombre: String(anioDe(c, s)),
          color: COLOR_SUFIJO[s], datos: hastaMesActual(MESES.map((m) => f[`${m}${s}`]), anioDe(c, s)) })) }) }]
    }
    return [{ alto: 460, opcion: lineasPorMes({ titulo, subtitulo, eje: 'Tasa',
      series: CATEGORIAS[d].map(([nombre], k) => ({ nombre, color: PALETA[k],
        datos: hastaMesActual(MESES.map((m) => f[`${m}Actual${k + 1}`]), c.anio) })) }) }]
  },
}

// ---------------------------------------------------------------------------------------
// 6. Situación laboral de las personas de 15 a 24 años (empleo)
//    Por año: cuatro columnas por año (estudian, trabajan, ambos, ninguno).
//    Por mes: cuatro tablas (una por grupo), cada una con el esquema común por mes.
// ---------------------------------------------------------------------------------------
const GRUPOS_NINI = [['se', 'Solo estudian', 'a', 'Est.'], ['st', 'Solo trabajan', 'b', 'Trab.'],
  ['et', 'Estudian y trabajan', 'c', 'Est.-trab.'], ['nini', 'Ni estudian ni trabajan', 'd', 'NINI']]

export const situacionLaboral = {
  tabla: (filas, c) => {
    if (c.vista === 'odei-mes') {
      return { secciones: GRUPOS_NINI.map(([g, titulo]) => ({ titulo: titulo.toUpperCase(),
        ...tablaPorMes(filas.filter((f) => f.grupo === g), c) })) }
    }
    const anios = aniosEn(filas, /^indicador(\d{4})a$/)
    return {
      fijas: 2,
      encabezados: [
        [{ texto: 'N°', filas: 3 }, { texto: nombreColumna(c), filas: 3 }, { texto: 'AÑOS', columnas: anios.length * 4 }],
        anios.map((a) => ({ texto: a, columnas: 4 })),
        anios.flatMap(() => GRUPOS_NINI.map(([, , , t]) => ({ texto: t }))),
      ],
      filas: filas.map((f, i) => ({ total: esTotal(f, i), celdas: [...celdasFijas(f, i, c),
        ...anios.flatMap((a) => GRUPOS_NINI.map(([, , x]) => ({ texto: num(f[`indicador${a}${x}`]) })))] })),
    }
  },
  graficos: (filas, c) => {
    if (c.vista === 'odei-mes') {
      if (c.nivel >= 4) return []
      return GRUPOS_NINI.map(([g, titulo]) => {
        const f = filas.find((x) => x.grupo === g)
        if (!f) return null
        const sufijos = c.nivel >= 3 ? ['Actual'] : SUFIJOS
        return { ancho: 'medio', alto: 420, opcion: tituloLargo(lineasPorMes({ titulo, subtitulo: subtituloFiltros(c),
          eje: 'Porcentaje %', series: sufijos.map((s) => ({ nombre: String(anioDe(c, s)), color: COLOR_SUFIJO[s],
            datos: hastaMesActual(MESES.map((m) => f[`${m}${s}`]), anioDe(c, s)) })) })) }
      }).filter(Boolean)
    }
    const f = filas[0]
    if (!f) return []
    const anios = aniosEn(filas, /^indicador(\d{4})a$/)
    const nombre = c.nivel === 1 ? f.nombreMostrar : (filas[1]?.nombreMostrar ?? c.nombreSede)
    if (c.vista === 'departamentos') {
      const ultimo = anios[anios.length - 1]
      return [
        { ancho: 'medio', alto: 440, opcion: barrasAgrupadas({ titulo: `Situación laboral de personas entre 15 y 24 años de edad - ${nombre}`,
          eje: 'Porcentaje %', anchoTitulo: 420, categorias: anios, series: GRUPOS_NINI.map(([, t, x]) => ({ nombre: t, datos: anios.map((a) => f[`indicador${a}${x}`]) })) }) },
        { ancho: 'medio', alto: 440, opcion: torta({ titulo: `Situación laboral de la población entre 15 y 24 años de edad en el año ${ultimo} - ${nombre}`,
          datos: GRUPOS_NINI.map(([, t, x]) => ({ nombre: t, valor: f[`indicador${ultimo}${x}`] })) }) },
      ]
    }
    return GRUPOS_NINI.map(([, t, x]) => ({ ancho: 'medio', alto: 400, opcion: barrasPorAnio({
      titulo: `Porcentaje de personas entre 15 a 24 años de edad\n${t} - ${nombre}`, eje: 'Porcentaje %', nombre: t, anios,
      valores: anios.map((a) => f[`indicador${a}${x}`]), colores: anios.map((_, k) => (k === anios.length - 1 ? '#B38B8B' : '#E0B7B7')) }) }))
  },
}

// ---------------------------------------------------------------------------------------
// 7. PET según condición de actividad, con factor y trimestre móvil (empleo)
//    Sin vistas: combos de ODEI y encuestador.
// ---------------------------------------------------------------------------------------
const TRIMESTRES = [['janfebmar', 'Nov-Dic-Ene'], ['febmarapr', 'Dic-Ene-Feb'], ['maraprmay', 'Ene-Feb-Mar'],
  ['aprmayjun', 'Feb-Mar-Abr'], ['mayjunjul', 'Mar-Abr-May'], ['junjulaug', 'Abr-May-Jun'],
  ['julaugsep', 'May-Jun-Jul'], ['augsepoct', 'Jun-Jul-Ago'], ['sepoctnov', 'Jul-Ago-Sep'],
  ['octnovdec', 'Ago-Sep-Oct'], ['novdecjan', 'Sep-Oct-Nov'], ['decjanfeb', 'Oct-Nov-Dic']]
const MESES_PET = ['ene', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
const CATEGORIAS_PET = ['EneFebMar', 'FebMarAbr', 'MarAbrMay', 'AbrMayJun', 'MayJunJul', 'JunJulAgo', 'JulAgoSet',
  'AgoSetOct', 'SetOctNov', 'OctNovDic', 'NovDicEne', 'DicEneFeb']

export const pet = {
  vistas: () => [],
  titulo: (c, { titulo }) => titulo,
  filtros: () => ['sede', 'encuestador'],
  consulta: (c) => ({ vista: c.pestana === 'tabular' ? 'trimestral' : 'pet',
    params: { indicador: 42, sede: String(c.filtros.sede ?? 0), usuario: String(c.filtros.encuestador ?? 0) } }),
  graficos: (filas) => {
    const anual = filas.filter((f) => f.serie === 'anual')
    const mensual = filas.filter((f) => f.serie === 'mensual')
    const barras = ['pet', 'pea', 'ocupados'].map((t) => ({ ancho: 'tercio', alto: 380, opcion: barrasPorAnio({
      titulo: t === 'ocupados' ? 'OCUPADOS' : t.toUpperCase(), eje: 'Porcentaje', nombre: 'Años',
      anios: anual.map((f) => f.anio), valores: anual.map((f) => f[t]), colores: '#D8E1BF' }) }))
    const lineas = ['pet', 'pea', 'ocupados'].map((t) => ({ ancho: 'tercio', alto: 380, opcion: {
      ...lineasPorMes({ titulo: t === 'ocupados' ? 'OCUPADOS' : t.toUpperCase(), eje: t.toUpperCase(),
        series: mensual.map((f, k) => ({ nombre: String(f.anio), color: PALETA[k % PALETA.length],
          datos: MESES_PET.map((m) => f[`${m}_${t}`]) })) }),
      xAxis: { type: 'category', data: CATEGORIAS_PET, axisLabel: { rotate: 45, fontSize: 9 } } } }))
    return [...barras, ...lineas]
  },
  tabla: (filas, c) => ({
    fijas: 2,
    encabezados: [
      [{ texto: 'N°', filas: 2 }, { texto: 'Indicadores', filas: 2 }, { texto: c.anio - 1, columnas: 12 }, { texto: c.anio, columnas: 12 }],
      [0, 1].flatMap(() => TRIMESTRES.map(([, t]) => ({ texto: t }))),
    ],
    // El procedimiento llama "…2016" al año anterior y "…2017" al año en curso
    filas: filas.map((f) => {
      const vacio = Number(f.idMostrar) === 0 && Number(f.orden) > 0
      return { total: Number(f.idMostrar) === 0, celdas: [
        { texto: Number(f.idMostrar) === 0 ? '' : f.idMostrar }, { texto: f.nombreMostrar, izquierda: true },
        ...[2016, 2017].flatMap((s) => TRIMESTRES.map(([k]) => ({ texto: vacio ? '-' : (f[`${k}${s}`] ?? '') }))),
      ] }
    }),
  }),
}

// ---------------------------------------------------------------------------------------
// 11. Etnicidad (empleo): filas largas (nombre, año, valor) que se ordenan en dos bloques:
//     distribución porcentual y número de casos, como la pantalla actual
// ---------------------------------------------------------------------------------------
const ETNIAS = ['Quechua', 'Aymara', 'Nativo o Indígena de la Amazonía', 'Negro/Moreno/Mulato/Zambo/Afroperuano',
  'Blanco', 'Mestizo', 'Otro', 'No Sabe']
const NOMBRE_VISTA_ETNIA = { departamentos: 'por departamentos', odei: '- Lima', 'odei-mes': 'por ODEI' }

function pivoteEtnicidad(filas) {
  const salida = []
  let actual = null
  let anterior = Infinity
  filas.forEach((f) => {
    const anio = Number(f.anio)
    if (!actual || actual.nombre !== f.nombre || (actual.bloque === 'casos' && anio <= anterior)) {
      actual = { nombre: f.nombre, orden: f.orden, pct: {}, casos: {}, bloque: 'pct' }
      salida.push(actual)
    } else if (anio <= anterior) {
      actual.bloque = 'casos'  // segunda pasada de años del mismo nombre: número de casos
    }
    actual[actual.bloque][anio] = f.indicador
    anterior = anio
  })
  return salida
}

export const etnicidad = {
  filtros: () => [...FILTROS_RANGO, 'excluir'],
  titulo: (c, { titulo }) => titulo,
  consulta: (c) => ({ vista: c.vista, params: { indicador: 36, ...rango(c), excluir: c.filtros.excluir } }),
  tabla: (filas, c) => {
    const anios = Array.from({ length: c.anio - 2011 }, (_, k) => 2012 + k)
    return {
      fijas: 1,
      encabezados: [
        [{ texto: 'Ubicación', filas: 2 }, { texto: 'Distrib. Porcentual (%)', columnas: anios.length },
          { texto: 'Número de casos', columnas: anios.length }],
        [...anios, ...anios].map((a) => ({ texto: a })),
      ],
      filas: pivoteEtnicidad(filas).map((r) => ({ total: !ETNIAS.includes(r.nombre), celdas: [
        { texto: r.nombre, izquierda: true },
        ...anios.map((a) => ({ texto: r.pct[a] == null ? '-' : num(r.pct[a]) })),
        ...anios.map((a) => ({ texto: r.casos[a] == null ? '-' : num(r.casos[a], 0) })),
      ] })),
    }
  },
  graficos: (filas, c) => {
    // Primera ubicación (orden 1), distribución porcentual por año
    const r = pivoteEtnicidad(filas).filter((x) => String(x.orden) === '1' && ETNIAS.includes(x.nombre))
    if (!r.length) return []
    const anios = Array.from({ length: c.anio - 2011 }, (_, k) => 2012 + k)
    return [{ alto: 480, opcion: barrasAgrupadas({ titulo: `Etnias - Perú ${NOMBRE_VISTA_ETNIA[c.vista] ?? ''}`,
      eje: 'Porcentaje', categorias: anios, sufijo: ' %',
      series: r.map((x) => ({ nombre: x.nombre, datos: anios.map((a) => x.pct[a]) })) }) }]
  },
}
