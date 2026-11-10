<script setup>
import { onMounted, ref, watch } from 'vue'
import api from '@/api/cobertura'
import { useIndicador } from '@/composables/useIndicador'
import FiltrosIndicador from '@/components/indicador/FiltrosIndicador.vue'
import GraficoIndicador from '@/components/indicador/GraficoIndicador.vue'
import TablaIndicador from '@/components/indicador/TablaIndicador.vue'
import MapaIndicador from '@/components/indicador/MapaIndicador.vue'

// Una sola vista para todos los indicadores de cobertura: cambia solo el código.
const props = defineProps({
  indicador: { type: String, required: true },
  titulo: { type: String, required: true },
})

const { filtros, resultado, puntosMapa, cargando, exportando, error, consultar, cargarMapa, exportar } =
  useIndicador(api, props.indicador, `cobertura/${props.indicador}`)

const info = ref({ niveles: ['departamento'], tiene_mapa: false })
const pestana = ref('grafico')

onMounted(async () => {
  const { data } = await api.indicadores()
  info.value = data.find((i) => i.codigo === props.indicador) ?? info.value
})

watch(pestana, (p) => {
  if (p === 'mapa' && !puntosMapa.value.length) cargarMapa()
})
</script>

<template>
  <h1 class="text-h5 mb-4">{{ titulo }}</h1>

  <FiltrosIndicador v-model="filtros" :niveles="info.niveles" :cargando="cargando" @consultar="consultar">
    <template #acciones>
      <v-btn
        variant="outlined"
        prepend-icon="mdi-microsoft-excel"
        :loading="exportando"
        :disabled="!resultado.filas.length"
        @click="exportar"
      >
        Exportar a Excel
      </v-btn>
    </template>
  </FiltrosIndicador>

  <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = ''">
    {{ error }}
  </v-alert>

  <v-card>
    <v-tabs v-model="pestana" color="primary">
      <v-tab value="grafico" prepend-icon="mdi-chart-bar">Gráfico</v-tab>
      <v-tab value="tabla" prepend-icon="mdi-table">Tabla</v-tab>
      <v-tab v-if="info.tiene_mapa" value="mapa" prepend-icon="mdi-map-outline">Mapa</v-tab>
    </v-tabs>
    <v-card-text>
      <v-progress-linear v-if="cargando" indeterminate color="primary" class="mb-2" />
      <v-tabs-window v-model="pestana">
        <v-tabs-window-item value="grafico">
          <GraficoIndicador :columnas="resultado.columnas" :filas="resultado.filas" />
        </v-tabs-window-item>
        <v-tabs-window-item value="tabla">
          <TablaIndicador :columnas="resultado.columnas" :filas="resultado.filas" :cargando="cargando" />
        </v-tabs-window-item>
        <v-tabs-window-item value="mapa">
          <MapaIndicador :puntos="puntosMapa" />
        </v-tabs-window-item>
      </v-tabs-window>
    </v-card-text>
  </v-card>
</template>
