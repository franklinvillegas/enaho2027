<script setup>
import { computed, ref } from 'vue'
import { clasificarColumnas, etiqueta } from '@/composables/datos'

const props = defineProps({
  columnas: { type: Array, required: true },
  filas: { type: Array, required: true },
  cargando: { type: Boolean, default: false },
})

const busqueda = ref('')
const encabezados = computed(() => {
  const { numericas } = clasificarColumnas(props.columnas, props.filas)
  return props.columnas.map((c) => ({
    title: etiqueta(c),
    key: c,
    align: numericas.includes(c) ? 'end' : 'start',
    sortable: true,
  }))
})
</script>

<template>
  <v-text-field
    v-model="busqueda"
    prepend-inner-icon="mdi-magnify"
    label="Buscar en la tabla"
    clearable
    class="mb-2"
    style="max-width: 360px"
  />
  <v-data-table
    :headers="encabezados"
    :items="filas"
    :search="busqueda"
    :loading="cargando"
    :items-per-page="25"
    density="compact"
    fixed-header
    height="520"
    no-data-text="Sin resultados para los filtros elegidos."
  />
</template>
