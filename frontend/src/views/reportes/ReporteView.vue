<script setup>
// Vista genérica de reportes con el diseño de las pantallas actuales:
//  - cobertura: control de visitas, omisión por capítulos, omisiones GPS, tipo de entrevista
//  - calidad: indicadores de vivienda y hogar, programas sociales, ...
// Lo que cambia entre una pantalla y otra (indicadores, vistas, pestañas, filtros, columnas,
// gráficos) está en su configuración (config/reportesCobertura/*.js, config/reportesCalidad/*.js).
// Aquí va lo común:
//  - estado en la dirección (vista, pestaña y nivel): funciona "Atrás" y se puede compartir
//  - una consulta a la vez, sin repetir la misma; ventana de espera mientras carga
//  - Excel .xlsx de la tabla que ya está en pantalla (no vuelve a consultar la base)
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart, MapChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent, ToolboxComponent,
  VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import api from '@/api/reportes'
import { mensajeError } from '@/api/http'
import { catalogos, registrarUso } from '@/api/comun'
import { useAuthStore } from '@/stores/auth'
import { opcionesMapaCalor, registrarMapaPeru } from '@/composables/mapaPeru'
import TablaReporte from '@/components/reportes/TablaReporte.vue'
import { CONFIGURACIONES as COBERTURA } from '@/config/reportesCobertura'
import { CONFIGURACIONES as CALIDAD } from '@/config/reportesCalidad'

use([BarChart, LineChart, MapChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent,
  ToolboxComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps({
  modulo: { type: String, default: 'cobertura' },
  pantalla: { type: String, required: true },
  titulo: { type: String, default: '' },
})
const cfg = { cobertura: COBERTURA, calidad: CALIDAD }[props.modulo][props.pantalla]
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const PANTALLA = `${props.modulo}/${props.pantalla}`

// ---- Filtros ----------------------------------------------------------------------------
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre',
  'Octubre', 'Noviembre', 'Diciembre']
const OPC_MES = [{ t: 'Seleccione', v: 0 }, ...MESES.map((m, i) => ({ t: m, v: i + 1 }))]
const OPC_PERIODO = [{ t: 'TODOS', v: 0 }, ...[1, 2, 3, 4, 5].map((p) => ({ t: String(p), v: p }))]
const ODEIS = ref([])
const filtros = reactive({ mes_inicio: 0, periodo_inicio: 0, mes_fin: 0, periodo_fin: 0, excluir: 0,
  sede: 0, mes: 0, periodo: 0 })
const aplicados = ref({ ...filtros })
const odeiUsuario = computed(() => Number(auth.usuario?.odei ?? 0))
const opcionesOdei = computed(() => (odeiUsuario.value
  ? ODEIS.value.filter((o) => Number(o.codigo) === odeiUsuario.value)
  : [{ codigo: '0', nombre: 'TODOS' }, ...ODEIS.value]))

// ---- Estado en la dirección ----------------------------------------------------------------
const q = computed(() => route.query)
// Indicador elegido en el combo (pantallas de calidad)
const indicador = computed(() => {
  const lista = cfg.indicadores ?? []
  return lista.some((i) => String(i.v) === q.value.indicador) ? Number(q.value.indicador) : lista[0]?.v ?? null
})
const vistasDe = (c) => (typeof cfg.vistas === 'function' ? cfg.vistas(c) : cfg.vistas) ?? []
// Si la vista elegida no existe para este indicador (p. ej. "Visualizar casos"), la primera
const vista = computed(() => {
  const lista = vistasDe({ indicador: indicador.value })
  return lista.some((v) => v.codigo === q.value.vista) ? q.value.vista : lista[0]?.codigo || ''
})
const pestana = computed(() => {
  const lista = cfg.pestanas(ctx.value)
  return lista.some((p) => p.codigo === q.value.pestana) ? q.value.pestana : lista[0].codigo
})
const ctx = computed(() => {
  const sede = q.value.sede || '0'
  const usuario = q.value.usuario || '0'
  const conglomerado = q.value.conglomerado || '0'
  const nivel = 1 + (sede !== '0') + (usuario !== '0') + (conglomerado !== '0')
  return {
    vista: vista.value, pestana: q.value.pestana, nivel, indicador: indicador.value,
    nombreIndicador: cfg.indicadores?.find((i) => i.v === indicador.value)?.t ?? '',
    sede, nombreSede: q.value.nombreSede || '', usuario, encuestador: q.value.encuestador || '',
    conglomerado, filtros: aplicados.value, anio: new Date().getFullYear(),
    odeiPermitida: (c) => !odeiUsuario.value || odeiUsuario.value === Number.parseInt(c, 10),
  }
})
function ir(cambios, reemplazar = false) {
  const query = { ...route.query, ...cambios }
  Object.keys(query).forEach((k) => (query[k] == null || query[k] === '' || query[k] === '0') && delete query[k])
  ;(reemplazar ? router.replace : router.push)({ query })
}
const cambiarVista = (v) => ir({ vista: v, sede: null, nombreSede: null, usuario: null, encuestador: null,
  conglomerado: null }, true)
const cambiarPestana = (p) => ir({ pestana: p }, true)
function cambiarIndicador(i) {
  // Si el nuevo indicador no tiene la vista actual ("Visualizar casos"), pasa a ODEI y por mes
  const lista = vistasDe({ indicador: Number(i) })
  const cambios = { indicador: String(i) }
  if (!lista.some((v) => v.codigo === vista.value)) {
    Object.assign(cambios, { vista: (lista.find((v) => v.codigo === 'odei-mes') ?? lista[0])?.codigo,
      sede: null, nombreSede: null, usuario: null, encuestador: null, conglomerado: null })
  }
  ir(cambios, true)
}
const migas = computed(() => {
  const c = ctx.value
  const m = [{ texto: 'NACIONAL', ir: c.nivel > 1 ? { sede: null, nombreSede: null, usuario: null, encuestador: null, conglomerado: null } : null }]
  if (c.nivel >= 2) m.push({ texto: c.nombreSede || c.sede, ir: c.nivel > 2 ? { usuario: null, encuestador: null, conglomerado: null } : null })
  if (c.nivel >= 3) m.push({ texto: c.encuestador || c.usuario, ir: c.nivel > 3 ? { conglomerado: null } : null })
  if (c.nivel >= 4) m.push({ texto: c.conglomerado })
  return m
})

// ---- Datos: una consulta a la vez y sin repetir la misma -----------------------------------
const filas = ref([])
const filasMapa = ref([])
const error = ref('')
const cargando = ref(false)
const exportando = ref(false)
let ultimaClave = ''
const consulta = computed(() => cfg.consulta({ ...ctx.value, pestana: pestana.value }))
async function cargar() {
  const c = consulta.value
  if (!c) return
  const clave = JSON.stringify(c)
  if (clave === ultimaClave) return
  ultimaClave = clave
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.tabla(props.modulo, props.pantalla, c.vista, c.params)
    if (clave === ultimaClave) filas.value = data.filas
  } catch (e) {
    error.value = mensajeError(e)
    filas.value = []
    ultimaClave = ''
  } finally {
    cargando.value = false
  }
}
const cargandoMapa = ref(false)
async function cargarMapa() {
  if (!cfg.mapa || filasMapa.value.length) return
  cargandoMapa.value = true
  try {
    await registrarMapaPeru()
    filasMapa.value = (await api.tabla(props.modulo, props.pantalla, cfg.mapa.vista, {})).data.filas
  } catch (e) {
    error.value = mensajeError(e)
  } finally {
    cargandoMapa.value = false
  }
}
function buscar() {
  aplicados.value = { ...filtros, sede: String(filtros.sede) }
  if (cfg.filtroSedeNavega && filtros.sede !== Number(ctx.value.sede)) {
    // En omisiones GPS el combo de ODEI cambia el nivel, como en la pantalla actual
    const o = opcionesOdei.value.find((x) => Number(x.codigo) === Number(filtros.sede))
    ir({ sede: Number(filtros.sede) ? String(filtros.sede).padStart(2, '0') : null,
      nombreSede: Number(filtros.sede) ? o?.nombre : null, usuario: null, encuestador: null, conglomerado: null })
  }
  ultimaClave = ''
  cargar()
}

// ---- Tabla, gráficos y Excel -----------------------------------------------------------------
const modelo = computed(() => cfg.tabla(filas.value, { ...ctx.value, pestana: pestana.value }))
const graficos = computed(() => (cfg.graficos ? cfg.graficos(filas.value, { ...ctx.value, pestana: pestana.value }) : []))
const opcionesMapa = computed(() => opcionesMapaCalor(filasMapa.value, cfg.mapa?.etiqueta ?? ''))
const filtrosVisibles = computed(() => cfg.filtros({ ...ctx.value, pestana: pestana.value }))
const ve = (nombre) => filtrosVisibles.value.includes(nombre)
const titulo = computed(() => cfg.titulo({ ...ctx.value, pestana: pestana.value }))
const textos = computed(() => (typeof cfg.textos === 'function' ? cfg.textos(ctx.value) : cfg.textos) ?? [])
const esTabla = computed(() => !['grafico', 'mapa'].includes(pestana.value))
const busqueda = ref('')
const cerrados = ref(new Set(cfg.gruposCerrados ?? []))
function alternar(grupo) {
  const s = new Set(cerrados.value)
  if (s.has(grupo)) s.delete(grupo)
  else s.add(grupo)
  cerrados.value = s
}
watch(() => props.pantalla, () => (cerrados.value = new Set(cfg.gruposCerrados ?? [])))

function textoFiltros() {
  const a = aplicados.value
  const partes = []
  if (ve('mes_inicio') && a.mes_inicio) partes.push(`Mes inicial: ${MESES[a.mes_inicio - 1]}`)
  if (ve('periodo_inicio') && a.periodo_inicio) partes.push(`Periodo inicial: ${a.periodo_inicio}`)
  if (ve('mes_fin') && a.mes_fin) partes.push(`Mes final: ${MESES[a.mes_fin - 1]}`)
  if (ve('periodo_fin') && a.periodo_fin) partes.push(`Periodo final: ${a.periodo_fin}`)
  if (ve('excluir')) partes.push(`Excluir: ${cfg.exclusiones?.find((e) => e.v === a.excluir)?.t ?? ''}`)
  if (ve('mes') && a.mes) partes.push(`Mes: ${MESES[a.mes - 1]}`)
  if (ve('periodo') && a.periodo) partes.push(`Periodo: ${a.periodo}`)
  return partes.join(' - ')
}
async function exportar() {
  exportando.value = true
  try {
    // Lo que se ve en pantalla (sin los grupos cerrados), celda por celda
    const visible = (c) => !c.grupo || !cerrados.value.has(c.grupo)
    const m = modelo.value
    const tabla = {
      titulo: cfg.tituloExcel ? cfg.tituloExcel({ ...ctx.value, pestana: pestana.value }) : titulo.value,
      nombre_archivo: (cfg.archivo ?? props.pantalla).replace(/[^\w\- ]/g, '-'),
      color: (cfg.colorEncabezado ?? '#0065A9').replace('#', ''),
      encabezados: m.encabezados.map((f) => f.filter(visible).map((c) => ({ texto: String(c.texto).replace(/\n/g, ' '),
        columnas: c.alternar && c.columnasCerrado && cerrados.value.has(c.alternar) ? c.columnasCerrado : (c.columnas ?? 1),
        filas: c.filas ?? 1 }))),
      filas: m.filas.map((f) => {
        const celdas = f.celdas.filter(visible)
        return { total: !!f.total, celdas: celdas.map((c) => String(c.texto ?? '')),
          resaltadas: celdas.flatMap((c, k) => (c.resaltado ? [k] : [])) }
      }),
      pie: [textoFiltros() ? `SELECCIÓN: ${textoFiltros()}` : ''],
    }
    const { data } = await api.excel(tabla)
    const url = URL.createObjectURL(data)
    Object.assign(document.createElement('a'), { href: url, download: `${tabla.nombre_archivo}.xlsx` }).click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = mensajeError(e)
  } finally {
    exportando.value = false
  }
}

// ---- Ventana de espera ---------------------------------------------------------------------
const ocupado = computed(() => cargando.value || cargandoMapa.value || exportando.value)
const mensajeEspera = computed(() => (exportando.value ? 'Generando Excel...' : 'Cargando información...'))
const segundos = ref(0)
let reloj = null
watch(ocupado, (si) => {
  clearInterval(reloj)
  segundos.value = 0
  if (si) reloj = setInterval(() => segundos.value++, 1000)
})

// ---- Alto de la tabla hasta el borde de la ventana ---------------------------------------------
const contenedorTabla = ref(null)
const altoTabla = ref(440)
function ajustarAlto() {
  const el = contenedorTabla.value
  if (!el || !el.offsetParent) return
  altoTabla.value = Math.max(320, Math.floor(window.innerHeight - (el.getBoundingClientRect().top + window.scrollY) - 24))
}
const observador = new ResizeObserver(() => ajustarAlto())

// ---- Ciclo de vida -----------------------------------------------------------------------------
watch(consulta, () => cargar(), { immediate: true })
watch(pestana, (p) => p === 'mapa' && cargarMapa(), { immediate: true })
watch([filas, pestana, error], () => nextTick(() => requestAnimationFrame(ajustarAlto)))
const salir = () => registrarUso(PANTALLA, 'salida')
onMounted(async () => {
  registrarUso(PANTALLA, 'ingreso')
  window.addEventListener('beforeunload', salir)
  window.addEventListener('resize', ajustarAlto)
  observador.observe(document.body)
  filtros.sede = odeiUsuario.value
  if (cfg.usaComboOdei) {
    try {
      ODEIS.value = (await catalogos.odeis()).data
    } catch { /* el combo queda vacío; la tabla funciona igual */ }
  }
})
onBeforeUnmount(() => {
  clearInterval(reloj)
  observador.disconnect()
  window.removeEventListener('resize', ajustarAlto)
  window.removeEventListener('beforeunload', salir)
  salir()
})
</script>

<template>
  <div class="reporte">
    <h5 class="titulo">{{ titulo }}</h5>

    <div v-if="cfg.indicadores?.length" class="indicador">
      <label for="cmb-indicador">INDICADORES:</label>
      <select id="cmb-indicador" :value="indicador" @change="cambiarIndicador($event.target.value)">
        <option v-for="i in cfg.indicadores" :key="i.v" :value="i.v">{{ i.t }}</option>
      </select>
    </div>

    <div v-if="vistasDe(ctx).length" class="vistas">
      <button v-for="v in vistasDe(ctx)" :key="v.codigo" :class="['btn-vista', { activo: vista === v.codigo }]"
        @click="cambiarVista(v.codigo)">{{ v.nombre }}</button>
    </div>

    <div class="pestanas">
      <button v-for="p in cfg.pestanas(ctx)" :key="p.codigo" :class="{ activa: pestana === p.codigo }"
        @click="cambiarPestana(p.codigo)">{{ p.nombre }}</button>
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

    <!-- Filtros de la vista y pestaña actuales -->
    <div v-if="filtrosVisibles.length && pestana !== 'mapa'" class="filtros">
      <label v-if="ve('sede')">ODEI:<select v-model.number="filtros.sede">
        <option v-for="o in opcionesOdei" :key="o.codigo" :value="Number(o.codigo)">{{ o.nombre }}</option></select></label>
      <label v-if="ve('mes')">Mes:<select v-model.number="filtros.mes">
        <option v-for="o in OPC_MES" :key="o.v" :value="o.v">{{ o.v ? o.t.toUpperCase() : 'SELECCIONE' }}</option></select></label>
      <label v-if="ve('periodo')">Periodo:<select v-model.number="filtros.periodo">
        <option v-for="o in OPC_PERIODO" :key="o.v" :value="o.v">{{ o.v ? `PERIODO ${o.v}` : 'SELECCIONE' }}</option></select></label>
      <label v-if="ve('mes_inicio')">Mes inicial:<select v-model.number="filtros.mes_inicio">
        <option v-for="o in OPC_MES" :key="o.v" :value="o.v">{{ o.t }}</option></select></label>
      <label v-if="ve('periodo_inicio')">Periodo inicial:<select v-model.number="filtros.periodo_inicio">
        <option v-for="o in OPC_PERIODO" :key="o.v" :value="o.v">{{ o.t }}</option></select></label>
      <label v-if="ve('mes_fin')">Mes final:<select v-model.number="filtros.mes_fin">
        <option v-for="o in OPC_MES" :key="o.v" :value="o.v">{{ o.t }}</option></select></label>
      <label v-if="ve('periodo_fin')">Periodo final:<select v-model.number="filtros.periodo_fin">
        <option v-for="o in OPC_PERIODO" :key="o.v" :value="o.v">{{ o.t }}</option></select></label>
      <label v-if="ve('excluir')" class="ancho">Exclusiones:<select v-model.number="filtros.excluir">
        <option v-for="o in cfg.exclusiones" :key="o.v" :value="o.v">{{ o.t }}</option></select></label>
      <button class="btn-buscar" :disabled="ocupado" @click="buscar">Buscar</button>
    </div>

    <!-- RESUMEN GRÁFICO -->
    <div v-if="pestana === 'grafico'" class="panel">
      <div class="graficos">
        <div v-for="(g, k) in graficos" :key="k" :class="['grafico', g.ancho ?? 'completo']">
          <v-chart :option="g.opcion" autoresize :style="{ height: `${g.alto ?? 420}px` }" />
        </div>
      </div>
      <!-- Objetivo y fórmula en cuadro (indicadores de calidad) -->
      <table v-if="cfg.textosEnCuadro && textos.length" class="cuadro-formula">
        <thead><tr><th>CATEGORÍA</th><th>DESCRIPCIÓN</th></tr></thead>
        <tbody v-for="(t, k) in textos" :key="k">
          <tr v-if="t.descripcion"><th>OBJETIVO</th><td>{{ t.descripcion }}</td></tr>
          <tr v-if="t.formula"><th>FÓRMULA</th><td>{{ t.formula }}</td></tr>
        </tbody>
      </table>
      <div v-for="(t, k) in cfg.textosEnCuadro ? [] : textos" :key="k" class="texto-indicador">
        <p v-if="t.descripcion"><b>Descripción:</b>&nbsp; {{ t.descripcion }}</p>
        <p v-if="t.formula"><b>Fórmulas:</b>&nbsp; {{ t.formula }}</p>
      </div>
    </div>

    <!-- TABLAS -->
    <div v-if="esTabla">
      <div v-if="ctx.nivel > 1" class="migas">
        <template v-for="(m, k) in migas" :key="k">
          <a v-if="m.ir" @click="ir(m.ir)">{{ m.texto }}</a><span v-else>{{ m.texto }}</span>
          <span v-if="k < migas.length - 1"> &gt; </span>
        </template>
      </div>
      <div class="exportar">
        <a :class="{ deshabilitado: exportando || !filas.length }" @click="exportar">
          <v-icon icon="mdi-microsoft-excel" color="#1D6F42" size="22" /> Exportar Excel
        </a>
        <slot name="acciones" :filas="filas" :ctx="ctx" />
      </div>
      <div class="buscar">
        <span>Buscar:</span>
        <v-text-field v-model="busqueda" placeholder="Escriba para Filtrar..." append-inner-icon="mdi-magnify"
          density="compact" variant="outlined" hide-details style="max-width: 240px" />
      </div>
      <div ref="contenedorTabla">
        <TablaReporte :modelo="modelo" :cerrados="cerrados" :busqueda="busqueda" :alto="altoTabla"
          :color="cfg.colorEncabezado ?? '#0065A9'" @ir="(e) => ir(e)" @alternar="alternar" />
      </div>
    </div>

    <!-- MAPA DE CALOR -->
    <div v-if="pestana === 'mapa'" class="panel mapa">
      <v-chart v-if="filasMapa.length" :option="opcionesMapa" autoresize style="height: 720px" />
      <p class="texto-indicador">Los departamentos con colores más oscuros representan el grupo de las tasas más
        altas y disminuyendo el color a tasas más bajas.</p>
    </div>
  </div>
</template>

<style scoped>
.reporte { font-family: Roboto, sans-serif; color: #333; }
.titulo { text-align: center; font-size: 1rem; font-weight: 700; padding-bottom: 6px; border-bottom: 1px solid #333; margin: 12px 0 0; }
.indicador { display: flex; justify-content: center; align-items: center; gap: 12px; margin: 22px 0 0; font-size: 0.85rem; }
.indicador select { width: min(620px, 100%); height: 32px; border: 1px solid #333; border-radius: 2px; padding: 0 10px;
  font-size: 0.82rem; background: #fff; appearance: auto; }
.cuadro-formula { margin: 18px auto 0; max-width: 760px; border-collapse: collapse; border: 3px solid #4C81C9; font-size: 0.85rem; }
.cuadro-formula th, .cuadro-formula td { border: 1px solid #ddd; padding: 8px 12px; }
.cuadro-formula thead th { background: #0065A9; color: #fff; text-align: center; }
.cuadro-formula td { text-align: center; }
.vistas { display: flex; justify-content: center; flex-wrap: wrap; margin: 24px 0 18px; }
.btn-vista { border: 1px solid #1E88E5; color: #1E88E5; background: #fff; padding: 7px 14px; font-size: 0.9rem; cursor: pointer; }
.btn-vista + .btn-vista { border-left: none; }
.btn-vista.activo { background: #1565C0; border-color: #1565C0; color: #fff; }
.pestanas { display: flex; flex-wrap: wrap; border-bottom: 1px solid #ddd; margin-bottom: 8px; }
.pestanas button { padding: 10px 18px; font-size: 0.82rem; color: #333; border: 1px solid transparent; border-bottom: none;
  background: none; cursor: pointer; text-transform: uppercase; }
.pestanas button.activa { border-color: #ddd; border-top: 2px solid #1E88E5; background: #fff; margin-bottom: -1px; }
.filtros { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; padding: 12px 0; }
.filtros label { display: flex; flex-direction: column; font-size: 0.85rem; flex: 1 1 160px; max-width: 260px; }
.filtros label.ancho { max-width: 320px; }
.filtros select { margin-top: 8px; height: 32px; border: 1px solid #333; border-radius: 2px; padding: 0 10px; font-size: 0.8rem;
  background: #fff; appearance: auto; }
.btn-buscar { background: #1565C0; color: #fff; border: none; border-radius: 3px; padding: 8px 20px; font-size: 0.9rem; cursor: pointer; }
.btn-buscar:disabled { opacity: 0.6; }
.espera { background: #fff; border-radius: 6px; padding: 24px 40px; text-align: center; box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25); min-width: 260px; }
.espera-texto { margin-top: 14px; font-size: 0.95rem; font-weight: 500; color: #333; }
.espera-tiempo { margin-top: 4px; font-size: 0.8rem; color: #777; }
.panel { border: 1px solid #ddd; border-radius: 2px; padding: 16px; }
.graficos { display: flex; flex-wrap: wrap; gap: 16px; justify-content: space-around; }
.grafico.completo { flex: 1 1 100%; }
.grafico.medio { flex: 1 1 440px; max-width: 49%; border: 1px solid #eee; padding: 8px; }
.texto-indicador { font-size: 0.88rem; margin-top: 12px; }
.texto-indicador p { margin: 4px 0; }
.migas { margin: 10px 0 0 12px; font-size: 0.9rem; font-weight: 700; }
.migas a { color: #1E88E5; cursor: pointer; }
.exportar { text-align: center; margin: 24px 0 8px; font-size: 0.8rem; font-weight: 700; display: flex; gap: 24px; justify-content: center; }
.exportar a { cursor: pointer; color: #000; }
.exportar a.deshabilitado { opacity: 0.5; pointer-events: none; }
.buscar { display: flex; justify-content: flex-end; align-items: center; gap: 6px; font-size: 0.85rem; margin-bottom: 6px; }
.mapa { max-width: 1140px; margin: 0 auto; }
@media (max-width: 960px) { .grafico.medio { max-width: 100%; } }
</style>
