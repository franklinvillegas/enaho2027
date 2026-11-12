<script setup>
// Pantallas de tasa de no respuesta (total, parcial): mismo diseño que las pantallas
// actuales (templates/.../tasaNoRespuesta/tnr_total.html y tnr_parcial.html). Una sola
// vista para todas: lo que cambia (procedimientos, columnas, textos, colores, filtros)
// lo envía el backend en /cobertura/<indicador>/. Mejoras frente a la pantalla actual:
//  - años y meses salen de los datos (no están escritos a mano)
//  - Excel real (.xlsx) generado en el servidor
//  - errores en pantalla, no con alert()
//  - la vista, la pestaña y el nivel quedan en la dirección: funciona "Atrás" y se comparte
//  - mapa sin servicios externos (antes Google GeoChart con clave expuesta)
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use, registerMap } from 'echarts/core'
import { BarChart, LineChart, MapChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent, ToolboxComponent,
  VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import apiTnr from '@/api/tasaNoRespuesta'
import { mensajeError } from '@/api/http'
import { registrarUso } from '@/api/comun'
import { useAuthStore } from '@/stores/auth'
import { MESES_CORTOS, aniosConMeses, aniosDe, colorCasilla, esFilaTotal, formatear, idFila,
  modeloColumnas, serieMensual, MESES } from '@/composables/tablaTnr'

use([BarChart, LineChart, MapChart, GridComponent, LegendComponent, TitleComponent,
  TooltipComponent, ToolboxComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps({
  indicador: { type: String, required: true }, // tnr-total, tnr-parcial
  titulo: { type: String, default: '' },
})

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const api = apiTnr(props.indicador)
const pantalla = `cobertura/${props.indicador}`

const info = ref({ titulo: props.titulo, descripcion: '', formula: '', vistas: [], prefijo: 'tnr',
  filtros_extra: [], colorear_ultimo: false, titulo_detalle: 'AÑOS', grafico: {} })
const g = computed(() => info.value.grafico)
const tieneFiltro = (nombre) => info.value.filtros_extra.includes(nombre)
const datos = ref({ columnas: [], filas: [] })
const cargando = ref(false)
const exportando = ref(false)
const cargandoMapa = ref(false)
const error = ref('')
const busqueda = ref('')

// Filtros del resumen tabular (mismos valores que la pantalla actual)
const filtros = reactive({ mes_inicio: 0, periodo_inicio: 0, mes_fin: 0, periodo_fin: 0,
  excluir: 0, solo_activos: false })
const OPC_MES = [{ title: 'Seleccione', value: 0 },
  ...MESES.map((m, i) => ({ title: m.toUpperCase(), value: i + 1 }))]
const OPC_PERIODO = [{ title: 'TODOS', value: 0 }, ...[1, 2, 3, 4, 5].map((p) => ({ title: String(p), value: p }))]
const OPC_EXCLUIR = [
  { title: 'Sin exclusiones', value: 0 },
  { title: 'Excluir no panel', value: 1 },
  { title: 'Excluir panel', value: 2 },
  { title: 'Excluir panel con resultado ausente y subresultado no tiene teléfono', value: 3 },
]
const OPC_ACTIVOS = [{ title: 'TODOS', value: false }, { title: 'ACTIVOS', value: true }]

// Estado en la dirección: vista, pestaña y nivel de navegación
const q = computed(() => route.query)
const vista = computed(() => q.value.vista || 'departamentos')
const pestana = computed(() => q.value.pestana || 'grafico')
const sede = computed(() => q.value.sede || '0')
const usuario = computed(() => q.value.usuario || '0')
const conglomerado = computed(() => q.value.conglomerado || '0')
const nivel = computed(() => (conglomerado.value !== '0' ? 4 : usuario.value !== '0' ? 3 : sede.value !== '0' ? 2 : 1))

function ir(cambios, reemplazar = false) {
  const query = { ...route.query, ...cambios }
  Object.keys(query).forEach((k) => (query[k] === '0' || query[k] == null) && delete query[k])
  ;(reemplazar ? router.replace : router.push)({ query })
}
const cambiarVista = (v) => ir({ vista: v, sede: null, nombreSede: null, usuario: null, encuestador: null, conglomerado: null })
const cambiarPestana = (p) => ir({ pestana: p }, true)

// Títulos y navegación (NACIONAL > SEDE > ENCUESTADOR > CONGLOMERADO)
const ambito = computed(() => {
  if (nivel.value === 1) return 'ÁMBITO NACIONAL'
  let t = `SEDE ${q.value.nombreSede || sede.value}`
  if (nivel.value >= 3) t += ` - ENCUESTADOR ${q.value.encuestador || usuario.value}`
  if (nivel.value === 4) t += ` - CONGLOMERADO ${conglomerado.value}`
  return t
})
const nombreGrafico = computed(() =>
  nivel.value === 1 ? 'NACIONAL' : nivel.value === 2 ? (q.value.nombreSede || sede.value)
    : (q.value.encuestador || usuario.value))
const migas = computed(() => {
  if (nivel.value === 1) return []
  const m = [{ texto: 'NACIONAL', ir: { sede: null, nombreSede: null, usuario: null, encuestador: null, conglomerado: null } }]
  m.push({ texto: q.value.nombreSede || sede.value, ir: { usuario: null, encuestador: null, conglomerado: null } })
  if (nivel.value >= 3) m.push({ texto: q.value.encuestador || usuario.value, ir: { conglomerado: null } })
  if (nivel.value === 4) m.push({ texto: conglomerado.value })
  return m
})

// Columnas
const modelo = computed(() => modeloColumnas(datos.value.columnas,
  { prefijo: info.value.prefijo, colorearUltimo: info.value.colorear_ultimo }))
const tituloAnios = computed(() => (nivel.value === 4 ? info.value.titulo_detalle : 'AÑOS'))
const columnaNombre = computed(() => {
  if (nivel.value === 1) return vista.value === 'departamentos'
    ? { clave: 'nombreMostrar', titulo: 'Dominios de estudio' } : { clave: 'nombreMostrar', titulo: 'ODEI' }
  if (nivel.value === 2) return { clave: 'encuestador', titulo: 'ENCUESTADOR' }
  return { clave: 'conglomerado', titulo: 'CONGLOMERADO' }
})
// Columnas que trae alguna fila (la fila del total a veces no trae mes, vivienda, hogar)
const presentes = computed(() => new Set(datos.value.filas.flatMap((f) => Object.keys(f))))
const soloPresentes = (cols) => cols.filter((c) => presentes.value.has(c.clave))
// Detalle de un conglomerado (nivel 4), como la pantalla actual:
// N° | MES | CONGLOMERADO | VIVIENDA | HOGAR | valores
const columnasExtraIzq = computed(() => (nivel.value === 4
  ? soloPresentes([{ clave: 'mes', titulo: 'MES' }]) : []))
const columnasTrasNombre = computed(() => (nivel.value === 4
  ? soloPresentes([{ clave: 'vivienda', titulo: 'VIVIENDA' }, { clave: 'hogar', titulo: 'HOGAR' }]) : []))
const columnasExtraDer = computed(() => (nivel.value === 3
  ? soloPresentes([{ clave: 'tipEnc', titulo: 'TIPO DE ENCUESTA' }, { clave: 'viv', titulo: 'VIVIENDAS TRABAJADAS' }])
  : []))
const totalColumnasDatos = computed(() => modelo.value.grupos.reduce((n, gr) => n + gr.columnas.length, 0))
const filasHeader = computed(() => (modelo.value.tipo === 'meses' ? 3 : 2))

const filasVisibles = computed(() => {
  const t = busqueda.value.trim().toLowerCase()
  const filas = datos.value.filas.map((f, i) => ({ f, i }))
  if (!t) return filas
  return filas.filter(({ f, i }) => i === 0 || Object.values(f).some((v) => String(v ?? '').toLowerCase().includes(t)))
})

// Igual que validarOdei() de la pantalla actual: un usuario de ODEI solo entra a la suya.
function odeiPermitida(codigo) {
  const propia = Number(auth.usuario?.odei ?? 0)
  return propia === 0 || propia === Number.parseInt(codigo, 10)
}
function esEnlace(fila, i) {
  if (esFilaTotal(fila, i, nivel.value)) return false
  if (nivel.value === 1) {
    return vista.value !== 'departamentos' && !String(fila.idMostrar).includes('.')
      && odeiPermitida(fila.idMostrar)
  }
  if (nivel.value === 2) return !!fila.usuario
  if (nivel.value === 3) return vista.value === 'odei-mes' && !!fila.conglomerado
  return false
}
function profundizar(fila) {
  if (nivel.value === 1) ir({ sede: String(fila.idMostrar), nombreSede: fila.nombreMostrar })
  else if (nivel.value === 2) ir({ usuario: String(fila.usuario), encuestador: fila.encuestador })
  else if (nivel.value === 3) ir({ conglomerado: String(fila.conglomerado) })
}

// Consulta
const parametros = () => ({ ...filtros, sede: sede.value, usuario: usuario.value, conglomerado: conglomerado.value })
async function consultar() {
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.vista(vista.value, parametros())
    datos.value = data
  } catch (e) {
    error.value = mensajeError(e)
    datos.value = { columnas: [], filas: [] }
  } finally {
    cargando.value = false
  }
}
async function exportar() {
  exportando.value = true
  try {
    const titulo = nivel.value === 1 ? 'NACIONAL' : ambito.value
    const { data } = await api.excel(vista.value, parametros(), datos.value.filas, titulo)
    const url = URL.createObjectURL(data)
    const prefijoArchivo = (g.value.archivo || g.value.serie_barras || props.indicador).replace(/_/g, '-').toUpperCase()
    const nombre = `${prefijoArchivo}-${ambito.value.replace(/[^A-Z0-9]+/gi, '-')}.xlsx`
    Object.assign(document.createElement('a'), { href: url, download: nombre }).click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = mensajeError(e)
  } finally {
    exportando.value = false
  }
}

// Gráfico (a partir de la primera fila: el total del nivel)
const opcionesGrafico = computed(() => {
  const fila = datos.value.filas[0]
  if (!fila) return null
  const conMeses = aniosConMeses(datos.value.columnas)
  if (conMeses.length) {
    const colores = ['#4A9BE0', '#000000', '#E57373', '#81C784']
    return {
      title: { text: `${g.value.titulo_lineas} - ${nombreGrafico.value}`, left: 'center', textStyle: { fontSize: 18 } },
      tooltip: { trigger: 'axis' },
      toolbox: { right: 10, feature: { saveAsImage: { title: 'Descargar' } } },
      legend: { bottom: 0 },
      grid: { left: 60, right: 30, top: 60, bottom: 60 },
      xAxis: { type: 'category', data: MESES_CORTOS },
      yAxis: { type: 'value', name: g.value.eje_lineas, nameLocation: 'middle', nameGap: 40 },
      series: conMeses.map((a, k) => ({
        name: String(a), type: 'line', color: colores[k % colores.length], symbolSize: 7,
        label: { show: true, position: 'top', fontWeight: 'bold', fontSize: 11, color: '#000' },
        data: serieMensual(fila, a),
      })),
    }
  }
  const anios = aniosDe(datos.value.columnas, info.value.prefijo)
  return {
    title: { text: `${g.value.titulo_barras} - ${nombreGrafico.value}`, left: 'center', textStyle: { fontSize: 18 } },
    tooltip: { trigger: 'axis', formatter: (p) => `${p[0].name}<br>${g.value.serie_barras}: <b>${Number(p[0].value).toFixed(1)}</b>` },
    toolbox: { right: 10, feature: { saveAsImage: { title: 'Descargar' } } },
    grid: { left: 60, right: 30, top: 60, bottom: 40 },
    xAxis: { type: 'category', data: anios.map(String) },
    yAxis: { type: 'value', name: g.value.eje_barras, nameLocation: 'middle', nameGap: 40 },
    series: [{
      name: g.value.serie_barras, type: 'bar', barWidth: '48%',
      emphasis: { itemStyle: { color: '#F7E1E1' } },
      label: { show: true, position: 'top', fontWeight: 'bold', fontSize: 11, color: '#000',
        formatter: (p) => `${Number(p.value).toFixed(1)}%` },
      // la última barra (año en curso) puede ir en otro color, como en la TNR parcial
      data: anios.map((a, k) => ({ value: fila[`${info.value.prefijo}${a}`],
        itemStyle: { color: k === anios.length - 1 ? g.value.color_barra_ultima : g.value.color_barras } })),
    }],
  }
})

// Mapa de calor por departamento
const mapaListo = ref(false)
const datosMapa = ref([])
const normalizar = (t) => String(t ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().trim()
async function cargarMapa() {
  cargandoMapa.value = true
  try {
    if (!mapaListo.value) {
      const geo = await (await fetch('/geo/peru_departamentos.geojson')).json()
      geo.features.forEach((f) => (f.properties.name = f.properties.NOMBDEP))
      registerMap('peru', geo)
      mapaListo.value = true
    }
    const { data } = await api.mapa()
    datosMapa.value = data.map((d) => ({ name: normalizar(d.departamento), value: Number(d.indicador) }))
  } catch (e) {
    error.value = mensajeError(e)
  } finally {
    cargandoMapa.value = false
  }
}

// Ventana de espera: tapa toda la vista mientras hay una consulta en curso, para que no
// se cambie de pestaña o de vista a medio cargar. No se puede cerrar; se va sola al terminar.
const ocupado = computed(() => cargando.value || cargandoMapa.value || exportando.value)
const mensajeEspera = computed(() => (exportando.value ? 'Generando Excel...' : 'Cargando información...'))
const segundos = ref(0)
let reloj = null
watch(ocupado, (si) => {
  clearInterval(reloj)
  segundos.value = 0
  if (si) reloj = setInterval(() => segundos.value++, 1000)
})
const opcionesMapa = computed(() => {
  const valores = datosMapa.value.map((d) => d.value)
  return {
    tooltip: { formatter: (p) => `<b>${p.name}</b><br>${g.value.etiqueta_mapa}: <b>${p.value ?? '-'}</b>` },
    visualMap: { min: Math.min(...valores), max: Math.max(...valores), left: 20, bottom: 20,
      orient: 'horizontal', calculable: false, text: [String(Math.max(...valores)), String(Math.min(...valores))],
      inRange: { color: ['#EFE8DF', '#3A95F7'] } },
    // aspectScale 1: Perú está cerca del ecuador y no necesita la corrección por defecto (0.75),
    // que lo dibujaba angosto
    series: [{ type: 'map', map: 'peru', roam: false, data: datosMapa.value,
      aspectScale: 1, layoutCenter: ['50%', '50%'], layoutSize: '98%',
      itemStyle: { borderColor: '#FFFFFF', areaColor: '#F4F4F4' },
      emphasis: { label: { show: false }, itemStyle: { areaColor: '#1565C0' } } }],
  }
})

// Alto de la tabla: ocupa todo el espacio libre hasta el borde inferior de la ventana
// (encabezado fijo y desplazamiento dentro de la tabla). Se recalcula al cambiar el
// tamaño de la ventana, la pestaña o los datos.
const contenedorTabla = ref(null)
const altoTabla = ref(440)
function ajustarAltoTabla() {
  const el = contenedorTabla.value
  if (!el || !el.offsetParent) return
  const arriba = el.getBoundingClientRect().top + window.scrollY
  altoTabla.value = Math.max(320, Math.floor(window.innerHeight - arriba - 24))
}
const reajustar = () => nextTick(() => requestAnimationFrame(ajustarAltoTabla))
watch([datos, pestana, nivel, cargando, error], reajustar)
window.addEventListener('resize', ajustarAltoTabla)
// Si algo de arriba cambia de alto (mensajes, ruta de navegación), la tabla se reacomoda
const observador = new ResizeObserver(() => ajustarAltoTabla())
onMounted(() => observador.observe(document.body))

// Ciclo de vida
onMounted(async () => {
  registrarUso(pantalla, 'ingreso')
  try {
    info.value = (await api.info()).data
  } catch (e) {
    error.value = mensajeError(e)
  }
})
watch([vista, sede, usuario, conglomerado], consultar, { immediate: true })
watch(pestana, (p) => p === 'mapa' && !datosMapa.value.length && cargarMapa(), { immediate: true })
const salir = () => registrarUso(pantalla, 'salida')
window.addEventListener('beforeunload', salir)
onMounted(reajustar)
onBeforeUnmount(() => {
  clearInterval(reloj)
  window.removeEventListener('resize', ajustarAltoTabla)
  observador.disconnect()
  window.removeEventListener('beforeunload', salir)
  salir()
})
</script>

<template>
  <div class="tnr">
    <h5 class="titulo">{{ info.titulo.toUpperCase() }} - {{ ambito }}</h5>

    <div class="d-flex justify-center my-6">
      <div class="grupo-vistas">
        <button
          v-for="v in info.vistas"
          :key="v.codigo"
          type="button"
          :class="['btn-vista', { activo: vista === v.codigo }]"
          @click="cambiarVista(v.codigo)"
        >
          {{ v.nombre }}
        </button>
      </div>
    </div>

    <div class="pestanas">
      <button :class="{ activa: pestana === 'grafico' }" @click="cambiarPestana('grafico')">RESUMEN GRÁFICO</button>
      <button :class="{ activa: pestana === 'tabular' }" @click="cambiarPestana('tabular')">RESUMEN TABULAR</button>
      <button :class="{ activa: pestana === 'mapa' }" @click="cambiarPestana('mapa')">MAPA DE CALOR</button>
    </div>

    <v-overlay :model-value="ocupado" persistent no-click-animation scrim="#000000" opacity="0.45"
      class="align-center justify-center" aria-live="polite">
      <div class="espera">
        <v-progress-circular indeterminate color="#1565C0" size="44" width="4" />
        <div class="espera-texto">{{ mensajeEspera }}</div>
        <div v-if="segundos >= 3" class="espera-tiempo">{{ segundos }} s</div>
      </div>
    </v-overlay>
    <v-alert v-if="error" type="error" variant="tonal" density="compact" class="my-3" closable @click:close="error = ''">
      {{ error }}
    </v-alert>

    <!-- RESUMEN GRÁFICO -->
    <div v-show="pestana === 'grafico'" class="panel">
      <v-chart v-if="opcionesGrafico" :option="opcionesGrafico" autoresize style="height: 420px" />
      <div v-if="info.descripcion" class="texto-indicador">
        <p><b>Descripción:</b>&nbsp; {{ info.descripcion }}</p>
        <p><b>Fórmulas:</b>&nbsp;&nbsp; {{ info.formula }}</p>
      </div>
    </div>

    <!-- RESUMEN TABULAR -->
    <div v-show="pestana === 'tabular'">
      <div class="filtros">
        <label>Mes inicial:<select v-model.number="filtros.mes_inicio"><option v-for="o in OPC_MES" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
        <label>Periodo inicial:<select v-model.number="filtros.periodo_inicio"><option v-for="o in OPC_PERIODO" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
        <label>Mes final:<select v-model.number="filtros.mes_fin"><option v-for="o in OPC_MES" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
        <label>Periodo final:<select v-model.number="filtros.periodo_fin"><option v-for="o in OPC_PERIODO" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
        <label v-if="vista === 'odei-mes' && tieneFiltro('excluir')">Exclusiones:<select v-model.number="filtros.excluir"><option v-for="o in OPC_EXCLUIR" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
        <button class="btn-buscar" :disabled="cargando" @click="consultar">Buscar</button>
      </div>
      <div v-if="vista === 'odei-mes' && nivel >= 2 && tieneFiltro('solo_activos')" class="filtros">
        <label>Encuestadores:<select v-model="filtros.solo_activos"><option v-for="o in OPC_ACTIVOS" :key="o.title" :value="o.value">{{ o.title }}</option></select></label>
      </div>

      <div v-if="migas.length" class="migas">
        <template v-for="(m, k) in migas" :key="k">
          <a v-if="m.ir" @click="ir(m.ir)">{{ m.texto }}</a><span v-else>{{ m.texto }}</span>
          <span v-if="k < migas.length - 1"> &gt; </span>
        </template>
      </div>

      <div class="exportar">
        <a :class="{ deshabilitado: exportando || !datos.filas.length }" @click="exportar">
          <v-icon icon="mdi-microsoft-excel" color="#1D6F42" size="22" /> Exportar Excel
        </a>
      </div>
      <div class="buscar">
        <span>Buscar:</span>
        <v-text-field v-model="busqueda" placeholder="Escriba para Filtrar..." append-inner-icon="mdi-magnify"
          density="compact" variant="outlined" hide-details style="max-width: 200px" />
      </div>

      <div ref="contenedorTabla" class="tabla-contenedor" :style="{ maxHeight: `${altoTabla}px` }">
        <table class="tabla-tnr">
          <thead>
            <tr>
              <th :rowspan="filasHeader" class="fijo c1">N°</th>
              <th v-for="c in columnasExtraIzq" :key="c.clave" :rowspan="filasHeader">{{ c.titulo }}</th>
              <th :rowspan="filasHeader" class="fijo c2">{{ columnaNombre.titulo }}</th>
              <th v-for="c in columnasTrasNombre" :key="c.clave" :rowspan="filasHeader">{{ c.titulo }}</th>
              <th :colspan="totalColumnasDatos">{{ tituloAnios }}</th>
              <th v-for="c in columnasExtraDer" :key="c.clave" :rowspan="filasHeader">{{ c.titulo }}</th>
            </tr>
            <tr v-if="modelo.tipo === 'meses'">
              <th v-for="grupo in modelo.grupos" :key="grupo.anio" :colspan="grupo.columnas.length">{{ grupo.anio }}</th>
            </tr>
            <tr>
              <template v-for="grupo in modelo.grupos" :key="grupo.anio ?? 'a'">
                <th v-for="c in grupo.columnas" :key="c.clave">{{ c.titulo }}</th>
              </template>
            </tr>
          </thead>
          <tbody>
            <tr v-for="{ f, i } in filasVisibles" :key="i" :class="esFilaTotal(f, i, nivel) ? 'total' : (i % 2 ? 'par' : 'impar')">
              <td class="fijo c1 centro">{{ esFilaTotal(f, i, nivel) ? '' : idFila(f, nivel) }}</td>
              <td v-for="c in columnasExtraIzq" :key="c.clave" class="centro">{{ f[c.clave] }}</td>
              <td class="fijo c2">
                <a v-if="esEnlace(f, i)" class="enlace" @click="profundizar(f)">{{ f[columnaNombre.clave] ?? f.nombreMostrar }}</a>
                <span v-else>{{ f[columnaNombre.clave] ?? f.nombreMostrar }}</span>
              </td>
              <td v-for="c in columnasTrasNombre" :key="c.clave" class="centro">{{ f[c.clave] }}</td>
              <template v-for="grupo in modelo.grupos" :key="grupo.anio ?? 'a'">
                <!-- En el detalle de un encuestador se resalta en rojo el mes del conglomerado -->
                <td v-for="c in grupo.columnas" :key="c.clave"
                  :class="['centro', { 'mes-trabajo': nivel === 3 && c.mes && f.mes === c.mes }]">
                  <template v-if="nivel === 1 && Number(idFila(f)) === 0 && i !== 0">-</template>
                  <span v-else-if="c.colorear" class="casilla"
                    :style="{ background: colorCasilla(f[c.clave]).fondo, color: colorCasilla(f[c.clave]).texto }">
                    {{ formatear(f[c.clave], c.tasa) }}
                  </span>
                  <template v-else>{{ formatear(f[c.clave], c.tasa) }}</template>
                </td>
              </template>
              <td v-for="c in columnasExtraDer" :key="c.clave" class="centro">{{ f[c.clave] }}</td>
            </tr>
            <tr v-if="!cargando && !datos.filas.length">
              <td :colspan="3 + totalColumnasDatos" class="centro sin-datos">Sin resultados para los filtros elegidos.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- MAPA DE CALOR -->
    <div v-show="pestana === 'mapa'" class="panel mapa">
      <v-chart v-if="mapaListo && datosMapa.length" :option="opcionesMapa" autoresize style="height: 720px" />
      <p class="texto-indicador">
        Los departamentos con colores más oscuros representan el grupo de las tasas más altas y
        disminuyendo el color a tasas más bajas.
      </p>
    </div>
  </div>
</template>

<style scoped>
.tnr { font-family: Roboto, sans-serif; color: #333; }
.titulo { text-align: center; font-size: 1rem; font-weight: 700; padding-bottom: 6px;
  border-bottom: 1px solid #333; margin: 12px 0 0; }
.grupo-vistas { display: inline-flex; }
.btn-vista { border: 1px solid #1E88E5; color: #1E88E5; background: #fff; padding: 8px 14px;
  font-size: 0.85rem; cursor: pointer; margin-left: -1px; }
.btn-vista:first-child { border-radius: 2px 0 0 2px; }
.btn-vista:last-child { border-radius: 0 2px 2px 0; }
.btn-vista:hover, .btn-vista.activo { background: #1565C0; border-color: #1565C0; color: #fff; font-weight: 500; }
.pestanas { display: flex; border-bottom: 1px solid #ddd; margin-bottom: 8px; }
.pestanas button { padding: 12px 18px; font-size: 0.82rem; color: #333; border: 1px solid transparent;
  border-bottom: none; background: none; cursor: pointer; }
.pestanas button.activa { border-color: #ddd; border-top: 2px solid #1E88E5; background: #fff; margin-bottom: -1px; }
.espera { background: #fff; border-radius: 6px; padding: 24px 40px; text-align: center;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25); min-width: 260px; }
.espera-texto { margin-top: 14px; font-size: 0.95rem; font-weight: 500; color: #333; }
.espera-tiempo { margin-top: 4px; font-size: 0.8rem; color: #777; }
.panel { border: 1px solid #ddd; border-radius: 3px; background: #fff; padding: 12px; }
.mapa { max-width: 1140px; margin: 0 auto; }
.texto-indicador { font-size: 0.85rem; margin-top: 8px; }
.texto-indicador p { margin: 0 0 4px; }
.filtros { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; padding-top: 16px; }
.filtros label { display: flex; flex-direction: column; font-size: 0.85rem; flex: 1 1 200px; max-width: 280px; }
.filtros select { margin-top: 8px; height: 32px; border: 1px solid #333; border-radius: 2px; padding: 0 10px;
  font-size: 0.8rem; background: #fff; appearance: auto; }
.btn-buscar { background: #1565C0; color: #fff; border: none; border-radius: 3px; padding: 10px 16px;
  font-size: 0.9rem; cursor: pointer; }
.btn-buscar:disabled { opacity: 0.6; }
.migas { font-weight: 700; margin: 12px 0 0 16px; font-size: 0.85rem; }
.migas a, .enlace { color: #1E88E5; cursor: pointer; text-decoration: none; }
.exportar { text-align: center; margin: 40px 0 8px; font-size: 0.8rem; font-weight: 700; }
.exportar a { cursor: pointer; color: #000; }
.exportar a.deshabilitado { opacity: 0.5; pointer-events: none; }
.buscar { display: flex; justify-content: flex-end; align-items: center; gap: 6px; font-size: 0.85rem; margin-bottom: 6px; }
.tabla-contenedor { overflow: auto; border-bottom: 1px solid #333; }
.tabla-tnr { border-collapse: separate; border-spacing: 0; font-size: 0.72rem; min-width: 100%; }
.tabla-tnr th { background: #0065A9; color: #fff; text-align: center; vertical-align: middle; padding: 10px 8px;
  font-weight: 700; border: 1px solid rgba(255, 255, 255, 0.25); white-space: nowrap; position: sticky; z-index: 2; }
.tabla-tnr thead tr:nth-child(1) th { top: 0; }
.tabla-tnr thead tr:nth-child(2) th { top: 38px; }
.tabla-tnr thead tr:nth-child(3) th { top: 76px; }
.tabla-tnr td { padding: 9px 8px; border: 1px solid #e3e3e3; white-space: nowrap; }
.tabla-tnr tr.total td { background: #F5FFBE; font-weight: 700; }
.tabla-tnr tr.par td { background: #EAEAEA; }
.tabla-tnr tr.impar td { background: #FFFFFF; }
.centro { text-align: center; }
.fijo { position: sticky; z-index: 1; }
th.fijo { z-index: 3; }
.c1 { left: 0; min-width: 48px; }
.c2 { left: 48px; min-width: 160px; }
.mes-trabajo { color: #FF2400; font-weight: 700; }
.casilla { display: inline-block; min-width: 70px; padding: 0 0.2em; }
.sin-datos { padding: 24px; color: #777; }
</style>
