<script setup>
// TNR según estrato: mismo diseño que la pantalla actual
// (templates/.../tasaNoRespuesta/tnr_estrato.html + tnr_estrato.js), con estas mejoras:
//  - años salen de los datos (antes 2017–2026 escritos a mano)
//  - Excel real (.xlsx) por pestaña, generado en el servidor
//  - errores en pantalla, no con alert(); validaciones de filtros también en el servidor
//  - pestaña y navegación en la dirección: funciona "Atrás" y se puede compartir
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent, ToolboxComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import api from '@/api/tnrEstrato'
import { mensajeError } from '@/api/http'
import { registrarUso } from '@/api/comun'
import { useAuthStore } from '@/stores/auth'
import { AREAS, ESTRATOS, MESES_CORTOS, aniosEstrato, areaDeOrden, esArea, esTotal, formatear,
  seriesArea, valoresAnio, valoresMes } from '@/composables/tablaEstrato'

use([BarChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent, ToolboxComponent, CanvasRenderer])

const PANTALLA = 'cobertura/tnr-estrato'
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const info = ref({ titulo: 'TNR SEGÚN ESTRATO', titulos: {}, exclusiones: [], odeis: [] })
const error = ref('')
const cargando = ref(0)
const exportando = ref(false)
const busqueda = ref('')

// ---- Filtros (los mismos de la pantalla actual) ----------------------------------------
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre',
  'Octubre', 'Noviembre', 'Diciembre']
const OPC_MES = [{ title: 'Seleccione', value: 0 }, ...MESES.map((m, i) => ({ title: m, value: i + 1 }))]
const OPC_PERIODO = [{ title: 'Seleccione', value: 0 }, ...[1, 2, 3, 4, 5].map((p) => ({ title: String(p), value: p }))]
const filtros = reactive({ mes_inicio: 0, periodo_inicio: 0, mes_fin: 0, periodo_fin: 0, excluir: 0 })
const aplicados = ref({ ...filtros }) // los que se usaron en la última búsqueda
const filtrosHogar = reactive({ odei: 0, mes: 0 })

const odeiUsuario = computed(() => Number(auth.usuario?.odei ?? 0))
const opcionesOdei = computed(() => {
  const todas = info.value.odeis.map((o) => ({ title: o.nombre, value: Number(o.codigo) }))
  return odeiUsuario.value ? todas.filter((o) => o.value === odeiUsuario.value) : [{ title: 'TODOS', value: 0 }, ...todas]
})
const odeiPermitida = (codigo) => !odeiUsuario.value || odeiUsuario.value === Number(codigo)
const nombreOdei = (codigo) => info.value.odeis.find((o) => Number(o.codigo) === Number(codigo))?.nombre ?? codigo

// ---- Estado en la dirección: pestaña y navegación de cada tabla -------------------------
const q = computed(() => route.query)
const pestana = computed(() => q.value.pestana || 'grafico')
const nav = computed(() => ({
  anual: { tipo: Number(q.value.at || 0), estrato: Number(q.value.ae || 0), odei: q.value.ao || '00' },
  mensual: { tipo: Number(q.value.mt || 0), estrato: Number(q.value.me || 0), odei: q.value.mo || '00',
    conglomerado: q.value.mc || '0' },
}))
function ir(cambios, reemplazar = false) {
  const query = { ...route.query, ...cambios }
  Object.keys(query).forEach((k) => (query[k] == null || ['0', '00'].includes(String(query[k]))) && delete query[k])
  ;(reemplazar ? router.replace : router.push)({ query })
}
const cambiarPestana = (p) => ir({ pestana: p }, true)

// Nivel de cada tabla (como tip / tipo2 en la pantalla actual)
const nivelAnual = computed(() => (nav.value.anual.tipo === 0 ? 1 : Number(nav.value.anual.odei) === 0 ? 2 : 3))
const nivelMensual = computed(() => {
  const n = nav.value.mensual
  if (n.tipo === 0) return 1
  if (Number(n.odei) === 0) return 2
  return n.conglomerado === '0' ? 3 : 4
})

// ---- Datos ----------------------------------------------------------------------------
const datosGrafico = ref([])
const datosAnual = ref([])
const datosMensual = ref([])
const datosHogar = ref([])
const hogarCargado = ref(false)

async function cargar(fn) {
  cargando.value++
  error.value = ''
  try {
    return await fn()
  } catch (e) {
    error.value = mensajeError(e)
    return null
  } finally {
    cargando.value--
  }
}
const paramsAnual = () => ({ ...aplicados.value, ...nav.value.anual })
const paramsMensual = () => ({ ...aplicados.value, ...nav.value.mensual })
const paramsHogar = () => ({ ...filtrosHogar })

// El gráfico usa los mismos datos que la tabla anual en el nivel nacional: si la tabla
// está en ese nivel se reutilizan, sin volver a llamar al procedimiento.
const cargarGrafico = () => cargar(async () => {
  datosGrafico.value = (await api.tabla('anual', { ...aplicados.value, tipo: 0, estrato: 0, odei: '00' })).data.filas
})
const cargarAnual = () => cargar(async () => {
  datosAnual.value = (await api.tabla('anual', paramsAnual())).data.filas
  if (nivelAnual.value === 1) datosGrafico.value = datosAnual.value
})
const cargarMensual = () => cargar(async () => { datosMensual.value = (await api.tabla('mensual', paramsMensual())).data.filas })
const cargarHogar = () => cargar(async () => {
  datosHogar.value = (await api.tabla('hogar', paramsHogar())).data.filas
  hogarCargado.value = true
})

// Las consultas van una tras otra, nunca dos a la vez sobre el mismo procedimiento
// (dos ejecuciones simultáneas de ENAHO2017_TNR_ESTRATO_V3 hacían fallar una).
async function cargarAnualYGrafico() {
  await cargarAnual()
  if (nivelAnual.value !== 1) await cargarGrafico()
}
function buscar() {
  aplicados.value = { ...filtros }
  mensualCargado.value = false // con filtros nuevos, la pestaña por mes se vuelve a consultar
  if (pestana.value === 'mensual') cargarMensual()
  else cargarAnualYGrafico()
}

// ---- Tabla anual (RESUMEN ESTRATO) -----------------------------------------------------
const aniosAnual = computed(() => aniosEstrato(datosAnual.value))
const tituloNombreAnual = computed(() => ['ESTRATOS SOCIOECONOMICOS', 'ODEI', 'CONGLOMERADO'][nivelAnual.value - 1])
function nombreAnual(f) {
  if (nivelAnual.value === 1) return esArea(f) ? f.NOMBAREA : ESTRATOS[Number(f.ESTRATO)]
  return nivelAnual.value === 2 ? f.NOMODEI : f.CONGLOME
}
function enlaceAnual(f) {
  if (nivelAnual.value === 1 && !esArea(f)) {
    return { at: areaDeOrden(Number(f.ORDEN)), ae: f.ESTRATO, ao: null }
  }
  if (nivelAnual.value === 2 && odeiPermitida(f.ODEI)) return { ao: f.ODEI }
  return null
}

// ---- Tabla por mes (RESUMEN POR MES) ---------------------------------------------------
function nombreMensual(f) {
  const n = nivelMensual.value
  if (n === 1) return esArea(f) ? f.NOMBAREA : ESTRATOS[Number(f.ESTRATO)]
  if (n === 2) return f.NOMODEI
  if (n === 3) return f.CONGLOME
  return esTotal(f) ? f.CONGLOME : f.VIVIENDA
}
function enlaceMensual(f) {
  const n = nivelMensual.value
  if (n === 1 && !esArea(f)) return { mt: areaDeOrden(Number(f.ORDEN)), me: f.ESTRATO, mo: null, mc: null }
  if (n === 2 && odeiPermitida(f.ODEI)) return { mo: f.ODEI, mc: null }
  if (n === 3 && !esTotal(f) && f.CONGLOME) return { mc: f.CONGLOME }
  return null
}
const anioActual = new Date().getFullYear()

// ---- Navegación (migas) y detalle para el Excel ----------------------------------------
const nombreArea = (tipo, estrato) => `${AREAS[tipo]} - ${ESTRATOS[estrato]}`
const migasAnual = computed(() => {
  const n = nav.value.anual
  const m = [{ texto: 'NACIONAL URBANO', ir: nivelAnual.value > 1 ? { at: null, ae: null, ao: null } : null }]
  if (nivelAnual.value >= 2) m.push({ texto: nombreArea(n.tipo, n.estrato), ir: nivelAnual.value > 2 ? { ao: null } : null })
  if (nivelAnual.value === 3) m.push({ texto: nombreOdei(n.odei) })
  return m
})
const migasMensual = computed(() => {
  const n = nav.value.mensual
  const nivel = nivelMensual.value
  const m = [{ texto: 'NACIONAL URBANO', ir: nivel > 1 ? { mt: null, me: null, mo: null, mc: null } : null }]
  if (nivel >= 2) m.push({ texto: nombreArea(n.tipo, n.estrato), ir: nivel > 2 ? { mo: null, mc: null } : null })
  if (nivel >= 3) m.push({ texto: nombreOdei(n.odei), ir: nivel > 3 ? { mc: null } : null })
  if (nivel === 4) m.push({ texto: n.conglomerado })
  return m
})
function textoFiltros() {
  const a = aplicados.value
  const partes = []
  if (a.mes_inicio) partes.push(`Mes inicial: ${MESES[a.mes_inicio - 1]}`)
  if (a.periodo_inicio) partes.push(`Periodo inicial: ${a.periodo_inicio}`)
  if (a.mes_fin) partes.push(`Mes final: ${MESES[a.mes_fin - 1]}`)
  if (a.periodo_fin) partes.push(`Periodo final: ${a.periodo_fin}`)
  partes.push(`Exclusión: ${info.value.exclusiones.find((e) => e.valor === a.excluir)?.nombre ?? ''}`)
  return partes.join(', ')
}
const detalle = computed(() => {
  if (pestana.value === 'hogar') {
    const odei = opcionesOdei.value.find((o) => o.value === filtrosHogar.odei)?.title ?? ''
    return `${odei} - ${filtrosHogar.mes ? MESES[filtrosHogar.mes - 1] : 'Anual'}`
  }
  const migas = (pestana.value === 'mensual' ? migasMensual : migasAnual).value.map((m) => m.texto).join(' - ')
  return `${migas}, ${textoFiltros()}`
})

// ---- Buscar en la tabla visible ----------------------------------------------------------
function filtrar(filas, nombre) {
  const t = busqueda.value.trim().toLowerCase()
  const lista = filas.map((f, i) => ({ f, i }))
  if (!t) return lista
  return lista.filter(({ f, i }) => i === 0 || String(nombre(f) ?? '').toLowerCase().includes(t)
    || Object.values(f).some((v) => String(v ?? '').toLowerCase().includes(t)))
}
const filasAnual = computed(() => filtrar(datosAnual.value, nombreAnual))
const filasMensual = computed(() => filtrar(datosMensual.value, nombreMensual))
const filasHogar = computed(() => filtrar(datosHogar.value, () => ''))
const COLUMNAS_HOGAR = [
  ['ID', 'Nª'], ['ANIO', 'Año'], ['ODEI', 'ODEI'], ['NOMODEI', 'Nombre ODEI'], ['DISTRITO', 'Distrito'],
  ['NOMAREAGEN', 'Area'], ['MES', 'Mes'], ['PERIODO', 'Periodo'], ['CONGLOME', 'Conglomerado'],
  ['VIVIENDA', 'Selección'], ['HOGAR', 'Hogar'], ['RESULTADO', 'Resultado'], ['TIPOVIVIENDA', 'Tipo vivienda'],
  ['ESTRATO', 'Estrato'], ['VIVIENDAS_CONGLOME', 'Cant. Viviendas'], ['TNR_CONGLOME', `TNR ${anioActual}`],
]

// ---- Excel ------------------------------------------------------------------------------
async function exportar() {
  exportando.value = true
  try {
    const tabla = pestana.value === 'grafico' ? 'anual' : pestana.value
    const params = { anual: paramsAnual, mensual: paramsMensual, hogar: paramsHogar }[tabla]()
    const { data } = await api.excel(tabla, params, detalle.value)
    const url = URL.createObjectURL(data)
    Object.assign(document.createElement('a'), { href: url, download: `TNR_segun_estrato_${tabla}.xlsx` }).click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = mensajeError(e)
  } finally {
    exportando.value = false
  }
}

// ---- Gráficos: total urbano, Lima Metropolitana y resto urbano ---------------------------
// Colores por año como los de la pantalla actual (paleta por defecto de Highcharts)
const COLORES = ['#7CB5EC', '#434348', '#90ED7D', '#F7A35C', '#8085E9', '#F15C80', '#E4D354', '#2B908F',
  '#F45B5B', '#91E8E1']
function opcionesArea(area) {
  const series = seriesArea(datosGrafico.value, area)
  return {
    color: COLORES,
    title: { text: AREAS[area], subtext: 'TNR : Estrato Socio-económico', left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'normal' } },
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v == null ? '-' : Number(v).toFixed(1)) },
    toolbox: { right: 10, feature: { saveAsImage: { title: 'Descargar' } } },
    legend: { bottom: 0, type: 'scroll' },
    grid: { left: 50, right: 20, top: 70, bottom: 50 },
    xAxis: { type: 'category', data: ['ESTRATO A', 'ESTRATO B', 'ESTRATO C', 'ESTRATO D', 'ESTRATO E'] },
    yAxis: { type: 'value', min: 0, name: 'TNR %', nameLocation: 'middle', nameGap: 35 },
    series: series.map((s) => ({ ...s, type: 'bar', barGap: '10%' })),
  }
}

// ---- Ventana de espera (igual que TNR total) ----------------------------------------------
const ocupado = computed(() => cargando.value > 0 || exportando.value)
const mensajeEspera = computed(() => (exportando.value ? 'Generando Excel...' : 'Cargando información...'))
const segundos = ref(0)
let reloj = null
watch(ocupado, (si) => {
  clearInterval(reloj)
  segundos.value = 0
  if (si) reloj = setInterval(() => segundos.value++, 1000)
})

// ---- Alto de la tabla hasta el borde de la ventana ---------------------------------------
const contenedores = ref({})
const altoTabla = ref(440)
function ajustarAltoTabla() {
  const el = contenedores.value[pestana.value]
  if (!el || !el.offsetParent) return
  const arriba = el.getBoundingClientRect().top + window.scrollY
  altoTabla.value = Math.max(320, Math.floor(window.innerHeight - arriba - 24))
}
const reajustar = () => nextTick(() => requestAnimationFrame(ajustarAltoTabla))
const observador = new ResizeObserver(() => ajustarAltoTabla())
watch([pestana, datosAnual, datosMensual, datosHogar, error], reajustar)

// ---- Ciclo de vida -----------------------------------------------------------------------
// Solo cuando cambia la navegación de cada tabla (cambiar de pestaña no vuelve a consultar)
watch(() => JSON.stringify(nav.value.anual), cargarAnual)
watch(() => JSON.stringify(nav.value.mensual), cargarMensual)
// Las pestañas "por mes" y "tabular" se consultan recién al abrirlas (la pantalla actual
// consultaba todo al entrar, y había que esperar las consultas que no se iban a ver)
const mensualCargado = ref(false)
watch(datosMensual, () => (mensualCargado.value = true))
watch(pestana, (p) => {
  if (p === 'mensual' && !mensualCargado.value) cargarMensual()
  if (p === 'hogar' && !hogarCargado.value) cargarHogar()
})
const salir = () => registrarUso(PANTALLA, 'salida')
onMounted(async () => {
  registrarUso(PANTALLA, 'ingreso')
  window.addEventListener('beforeunload', salir)
  window.addEventListener('resize', ajustarAltoTabla)
  observador.observe(document.body)
  filtrosHogar.odei = odeiUsuario.value
  await cargar(async () => { info.value = (await api.info()).data })
  await cargarAnualYGrafico()
  if (pestana.value === 'mensual') await cargarMensual()
  if (pestana.value === 'hogar') await cargarHogar()
  reajustar()
})
onBeforeUnmount(() => {
  clearInterval(reloj)
  observador.disconnect()
  window.removeEventListener('resize', ajustarAltoTabla)
  window.removeEventListener('beforeunload', salir)
  salir()
})
</script>

<template>
  <div class="tnre">
    <h5 class="titulo">{{ info.titulo }}</h5>

    <!-- Filtros: los de la pantalla actual (en la pestaña de hogares cambian) -->
    <div v-if="pestana !== 'hogar'" class="filtros">
      <label>Mes inicial:<select v-model.number="filtros.mes_inicio"><option v-for="o in OPC_MES" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
      <label>Periodo inicial:<select v-model.number="filtros.periodo_inicio"><option v-for="o in OPC_PERIODO" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
      <label>Mes final:<select v-model.number="filtros.mes_fin"><option v-for="o in OPC_MES" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
      <label>Periodo final:<select v-model.number="filtros.periodo_fin"><option v-for="o in OPC_PERIODO" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
      <label class="ancho">Excluir:<select v-model.number="filtros.excluir"><option v-for="o in info.exclusiones" :key="o.valor" :value="o.valor">{{ o.nombre }}</option></select></label>
      <button class="btn-buscar" :disabled="ocupado" @click="buscar">Buscar</button>
    </div>
    <div v-else class="filtros">
      <label>ODEI:<select v-model.number="filtrosHogar.odei"><option v-for="o in opcionesOdei" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
      <label>Mes:<select v-model.number="filtrosHogar.mes"><option v-for="o in OPC_MES" :key="o.value" :value="o.value">{{ o.title }}</option></select></label>
      <button class="btn-buscar" :disabled="ocupado" @click="cargarHogar">Buscar</button>
    </div>

    <div class="pestanas">
      <button :class="{ activa: pestana === 'grafico' }" @click="cambiarPestana('grafico')"><v-icon icon="mdi-chart-bar" size="16" class="mr-2" />RESUMEN GRÁFICO</button>
      <button :class="{ activa: pestana === 'anual' }" @click="cambiarPestana('anual')"><v-icon icon="mdi-table" size="16" class="mr-2" />RESUMEN ESTRATO</button>
      <button :class="{ activa: pestana === 'mensual' }" @click="cambiarPestana('mensual')"><v-icon icon="mdi-table" size="16" class="mr-2" />RESUMEN POR MES</button>
      <button :class="{ activa: pestana === 'hogar' }" @click="cambiarPestana('hogar')"><v-icon icon="mdi-table" size="16" class="mr-2" />RESUMEN TABULAR</button>
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

    <!-- RESUMEN GRÁFICO: total urbano arriba; Lima Metropolitana y resto urbano abajo -->
    <div v-show="pestana === 'grafico'" class="graficos">
      <template v-if="datosGrafico.length">
        <div class="grafico-centro"><v-chart :option="opcionesArea(1)" autoresize style="height: 400px" /></div>
        <div class="graficos-fila">
          <v-chart :option="opcionesArea(2)" autoresize style="height: 400px" />
          <v-chart :option="opcionesArea(3)" autoresize style="height: 400px" />
        </div>
      </template>
    </div>

    <!-- Barra común de las tablas: navegación, Excel y búsqueda -->
    <template v-if="pestana !== 'grafico'">
      <div v-if="pestana !== 'hogar'" class="migas">
        <template v-for="(m, k) in (pestana === 'mensual' ? migasMensual : migasAnual)" :key="k">
          <v-icon v-if="k === 0" icon="mdi-home-outline" size="16" class="mr-1" />
          <a v-if="m.ir" @click="ir(m.ir)">{{ m.texto }}</a><span v-else>{{ m.texto }}</span>
          <span v-if="k < (pestana === 'mensual' ? migasMensual : migasAnual).length - 1" class="sep"> / </span>
        </template>
      </div>
      <div class="exportar">
        <a :class="{ deshabilitado: exportando }" @click="exportar">
          <v-icon icon="mdi-microsoft-excel" color="#1D6F42" size="22" /> Exportar Excel
        </a>
      </div>
      <div class="buscar">
        <span>Buscar:</span>
        <v-text-field v-model="busqueda" placeholder="Escriba para Filtrar..." append-inner-icon="mdi-magnify"
          density="compact" variant="outlined" hide-details style="max-width: 200px" />
      </div>
    </template>

    <!-- RESUMEN ESTRATO (anual) -->
    <div v-show="pestana === 'anual'" :ref="(el) => (contenedores.anual = el)" class="tabla-contenedor" :style="{ maxHeight: `${altoTabla}px` }">
      <table class="tabla">
        <thead>
          <tr>
            <th rowspan="2" class="fijo">{{ tituloNombreAnual }}</th>
            <th v-for="a in aniosAnual" :key="a" colspan="6">{{ a }}</th>
          </tr>
          <tr>
            <template v-for="a in aniosAnual" :key="a">
              <th>TOTAL</th><th>TOTAL_ABS</th><th>PANEL</th><th>PANEL_ABS</th><th>NO PANEL</th><th>NO PANEL_ABS</th>
            </template>
          </tr>
        </thead>
        <tbody>
          <tr v-for="{ f, i } in filasAnual" :key="i" :class="{ total: esTotal(f), area: nivelAnual === 1 && esArea(f), par: i % 2 }">
            <td class="fijo nombre">
              <a v-if="enlaceAnual(f)" class="enlace" @click="ir(enlaceAnual(f))">{{ nombreAnual(f) }}</a>
              <span v-else>{{ nombreAnual(f) }}</span>
            </td>
            <template v-for="a in aniosAnual" :key="a">
              <td v-for="(c, k) in valoresAnio(f, a)" :key="k" class="centro">{{ formatear(c.v, c.tasa) }}</td>
            </template>
          </tr>
          <tr v-if="!cargando && !datosAnual.length"><td :colspan="1 + aniosAnual.length * 6" class="sin-datos">Sin resultados para los filtros elegidos.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- RESUMEN POR MES -->
    <div v-show="pestana === 'mensual'" :ref="(el) => (contenedores.mensual = el)" class="tabla-contenedor" :style="{ maxHeight: `${altoTabla}px` }">
      <table class="tabla">
        <thead>
          <tr>
            <th rowspan="2" class="fijo">ESTRATOS<br>SOCIOECONOMICOS</th>
            <th rowspan="2">TOTAL<br>{{ anioActual }}</th>
            <th colspan="26">PANEL</th>
            <th colspan="26">NO PANEL</th>
          </tr>
          <tr>
            <template v-for="g in [['TOTAL', 'PANEL'], ['TOTAL', 'NO', 'PANEL']]" :key="g.length">
              <th><template v-for="(l, k) in g" :key="k"><br v-if="k">{{ l }}</template></th><th>Abs</th>
              <template v-for="m in MESES_CORTOS" :key="m"><th>{{ m }}</th><th>Abs</th></template>
            </template>
          </tr>
        </thead>
        <tbody>
          <tr v-for="{ f, i } in filasMensual" :key="i" :class="{ total: esTotal(f), area: nivelMensual === 1 && esArea(f), par: i % 2 }">
            <td :class="['fijo', 'nombre', { centro: nivelMensual === 4 || (nivelMensual === 1 && esArea(f)) }]">
              <a v-if="enlaceMensual(f)" class="enlace" @click="ir(enlaceMensual(f))">{{ nombreMensual(f) }}</a>
              <span v-else>{{ nombreMensual(f) }}</span>
            </td>
            <td v-for="(c, k) in valoresMes(f)" :key="k" class="centro">{{ formatear(c.v, c.tasa) }}</td>
          </tr>
          <tr v-if="mensualCargado && !cargando && !datosMensual.length"><td colspan="54" class="sin-datos">Sin resultados para los filtros elegidos.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- RESUMEN TABULAR (hogares) -->
    <div v-show="pestana === 'hogar'" :ref="(el) => (contenedores.hogar = el)" class="tabla-contenedor" :style="{ maxHeight: `${altoTabla}px` }">
      <table class="tabla hogar">
        <thead><tr><th v-for="[c, t] in COLUMNAS_HOGAR" :key="c">{{ t }}</th></tr></thead>
        <tbody>
          <tr v-for="{ f, i } in filasHogar" :key="i" :class="{ par: i % 2 }">
            <td v-for="[c] in COLUMNAS_HOGAR" :key="c" class="centro">{{ f[c] ?? '' }}</td>
          </tr>
          <tr v-if="hogarCargado && !cargando && !datosHogar.length"><td :colspan="COLUMNAS_HOGAR.length" class="sin-datos">Sin resultados para los filtros elegidos.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.tnre { font-family: Roboto, sans-serif; color: #333; }
.titulo { text-align: center; font-size: 1rem; font-weight: 700; padding-bottom: 6px;
  border-bottom: 1px solid #333; margin: 12px 0 0; }
.filtros { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; padding: 16px 0 12px; }
.filtros label { display: flex; flex-direction: column; font-size: 0.85rem; flex: 1 1 160px; max-width: 220px; }
.filtros label.ancho { max-width: 340px; flex-basis: 260px; }
.filtros select { margin-top: 8px; height: 32px; border: 1px solid #333; border-radius: 2px; padding: 0 10px;
  font-size: 0.8rem; background: #fff; appearance: auto; }
.btn-buscar { background: #fff; color: #1E88E5; border: 1px solid #1E88E5; border-radius: 3px; padding: 7px 16px;
  font-size: 0.9rem; cursor: pointer; }
.btn-buscar:hover { background: #1E88E5; color: #fff; }
.btn-buscar:disabled { opacity: 0.6; }
.pestanas { display: flex; flex-wrap: wrap; border-bottom: 1px solid #ddd; margin-bottom: 8px; }
.pestanas button { display: inline-flex; align-items: center; padding: 10px 16px; font-size: 0.82rem; color: #333;
  border: 1px solid transparent; border-bottom: none; background: none; cursor: pointer; }
.pestanas button.activa { border-color: #ddd; border-top: 2px solid #1E88E5; background: #fff; margin-bottom: -1px; }
.espera { background: #fff; border-radius: 6px; padding: 24px 40px; text-align: center;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25); min-width: 260px; }
.espera-texto { margin-top: 14px; font-size: 0.95rem; font-weight: 500; color: #333; }
.espera-tiempo { margin-top: 4px; font-size: 0.8rem; color: #777; }
.graficos { padding: 8px 0; }
.grafico-centro { max-width: 640px; margin: 0 auto 16px; }
.graficos-fila { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; }
.migas { margin: 8px 0 0 8px; font-size: 0.85rem; display: flex; align-items: center; flex-wrap: wrap; }
.migas a, .enlace { color: #1E88E5; cursor: pointer; text-decoration: none; }
.migas .sep { margin: 0 6px; color: #999; }
.exportar { text-align: center; margin: 16px 0 8px; font-size: 0.8rem; font-weight: 700; }
.exportar a { cursor: pointer; color: #000; }
.exportar a.deshabilitado { opacity: 0.5; pointer-events: none; }
.buscar { display: flex; justify-content: flex-end; align-items: center; gap: 6px; font-size: 0.85rem; margin-bottom: 6px; }
.tabla-contenedor { overflow: auto; border-bottom: 1px solid #ddd; }
.tabla { border-collapse: separate; border-spacing: 0; font-size: 0.72rem; min-width: 100%; text-transform: uppercase; }
.tabla thead { position: sticky; top: 0; z-index: 2; }
.tabla th { background: #1565C0; color: #fff; text-align: center; vertical-align: middle; padding: 8px 6px;
  font-weight: 700; border: 1px solid #ddd; white-space: nowrap; }
.tabla.hogar { text-transform: none; }
.tabla td { padding: 7px 6px; border: 1px solid #ddd; white-space: nowrap; background: #fff; }
.tabla tr.par td { background: #F9F9F9; }
.tabla tr.area td { font-weight: 700; }
.tabla tr.total td { background: #F5FFBE; font-weight: 700; }
.centro { text-align: center; }
.fijo { position: sticky; left: 0; z-index: 1; }
th.fijo { z-index: 3; min-width: 170px; }
.nombre { min-width: 170px; }
.sin-datos { padding: 24px; color: #777; text-align: center; }
</style>
