import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { mensajeError } from '@/api/http'
import { registrarUso } from '@/api/comun'

/**
 * Lógica común de una pantalla de indicador: filtros, consulta, exportación y mapa.
 * Recibe el cliente del módulo (p. ej. api/cobertura.js) para poder reutilizarse en
 * calidad, valores monetarios, etc.
 */
export function useIndicador(api, codigo, pantalla) {
  const hoy = new Date()
  const filtros = reactive({
    nivel: 'departamento',
    periodo_inicio: 1,
    periodo_fin: 1,
    mes_inicio: 1,
    mes_fin: hoy.getMonth() + 1,
    odei: null,
    encuestador: null,
    conglomerado: null,
    solo_activos: false,
  })
  const resultado = ref({ columnas: [], filas: [] })
  const puntosMapa = ref([])
  const cargando = ref(false)
  const exportando = ref(false)
  const error = ref('')

  const limpios = () =>
    Object.fromEntries(Object.entries(filtros).filter(([, v]) => v !== null && v !== ''))

  async function consultar() {
    cargando.value = true
    error.value = ''
    try {
      const { data } = await api.datos(codigo, limpios())
      resultado.value = data
    } catch (e) {
      error.value = mensajeError(e)
      resultado.value = { columnas: [], filas: [] }
    } finally {
      cargando.value = false
    }
  }

  async function cargarMapa() {
    try {
      const { data } = await api.mapa(codigo)
      puntosMapa.value = data
    } catch (e) {
      error.value = mensajeError(e)
    }
  }

  async function exportar() {
    exportando.value = true
    try {
      const { data } = await api.excel(codigo, limpios())
      const url = URL.createObjectURL(data)
      const a = Object.assign(document.createElement('a'), {
        href: url,
        download: `${codigo}_${filtros.nivel}.xlsx`,
      })
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      error.value = mensajeError(e)
    } finally {
      exportando.value = false
    }
  }

  onMounted(() => registrarUso(pantalla, 'ingreso'))
  onBeforeUnmount(() => registrarUso(pantalla, 'salida'))

  return { filtros, resultado, puntosMapa, cargando, exportando, error, consultar, cargarMapa, exportar }
}
