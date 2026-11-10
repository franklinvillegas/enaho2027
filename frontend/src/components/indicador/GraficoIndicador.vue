<script setup>
import { computed, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { clasificarColumnas, etiqueta, medidaPrincipal } from '@/composables/datos'

use([BarChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer])

const props = defineProps({
  columnas: { type: Array, required: true },
  filas: { type: Array, required: true },
})

// Una medida a la vez (mezclar conteos y tasas en un mismo eje oculta la tasa).
// Por defecto se muestra la tasa o porcentaje; el usuario puede elegir otra medida.
const tipos = computed(() => clasificarColumnas(props.columnas, props.filas))
const medidas = computed(() => tipos.value.numericas.map((c) => ({ title: etiqueta(c), value: c })))
const medida = ref(null)
watch(
  () => props.columnas,
  () => (medida.value = medidaPrincipal(tipos.value.numericas)),
  { immediate: true },
)

const opciones = computed(() => {
  const eje = tipos.value.categoricas[0]
  const filas = [...props.filas].sort((a, b) => Number(b[medida.value]) - Number(a[medida.value]))
  const muchas = filas.length > 12
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 56, right: 16, top: 24, bottom: muchas ? 100 : 40 },
    xAxis: {
      type: 'category',
      data: filas.map((f) => f[eje]),
      axisLabel: { rotate: muchas ? 45 : 0 },
    },
    yAxis: { type: 'value', name: etiqueta(medida.value ?? '') },
    dataZoom: filas.length > 30 ? [{ type: 'slider' }] : [],
    series: [
      {
        name: etiqueta(medida.value ?? ''),
        type: 'bar',
        data: filas.map((f) => Number(f[medida.value])),
        itemStyle: { color: '#1F4E79', borderRadius: [3, 3, 0, 0] },
        label: { show: !muchas, position: 'top' },
      },
    ],
  }
})
</script>

<template>
  <template v-if="filas.length && medida">
    <v-select
      v-if="medidas.length > 1"
      v-model="medida"
      :items="medidas"
      label="Medida"
      class="mt-2"
      style="max-width: 280px"
    />
    <v-chart :option="opciones" autoresize style="height: 420px" />
  </template>
  <v-alert v-else type="info" variant="tonal">Sin datos para graficar. Elija los filtros y consulte.</v-alert>
</template>
