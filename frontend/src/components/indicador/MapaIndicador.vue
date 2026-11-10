<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import L from 'leaflet'
import { columnasCoordenadas, etiqueta } from '@/composables/datos'

const props = defineProps({ puntos: { type: Array, required: true } })
const contenedor = ref(null)
let mapa = null
let capa = null

const columnas = computed(() => (props.puntos[0] ? Object.keys(props.puntos[0]) : []))
const coords = computed(() => columnasCoordenadas(columnas.value))
const tieneCoordenadas = computed(() => !!(coords.value.lat && coords.value.lon))

function dibujar() {
  if (!contenedor.value || !tieneCoordenadas.value) return
  if (!mapa) {
    mapa = L.map(contenedor.value).setView([-9.19, -75.02], 5) // Perú
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(mapa)
  }
  capa?.remove()
  capa = L.layerGroup(
    props.puntos.map((p) => {
      const texto = Object.entries(p)
        .map(([k, v]) => `<b>${etiqueta(k)}:</b> ${v ?? ''}`)
        .join('<br>')
      return L.circleMarker([Number(p[coords.value.lat]), Number(p[coords.value.lon])], {
        radius: 6,
      }).bindPopup(texto)
    }),
  ).addTo(mapa)
}

watch(() => props.puntos, () => nextTick(dibujar), { immediate: true })
onBeforeUnmount(() => mapa?.remove())
</script>

<template>
  <div v-if="tieneCoordenadas" ref="contenedor" style="height: 520px; border-radius: 4px" />
  <v-alert v-else-if="puntos.length" type="info" variant="tonal">
    Los datos del mapa no traen coordenadas. Columnas recibidas: {{ columnas.join(', ') }}.
    Se ajusta cuando se revise el procedimiento del mapa.
  </v-alert>
  <v-alert v-else type="info" variant="tonal">Sin datos de mapa.</v-alert>
</template>
