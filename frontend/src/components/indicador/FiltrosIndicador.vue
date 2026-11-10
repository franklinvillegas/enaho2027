<script setup>
import { computed, onMounted, ref } from 'vue'
import { catalogos } from '@/api/comun'

const filtros = defineModel({ type: Object, required: true })
const props = defineProps({
  niveles: { type: Array, default: () => ['departamento'] },
  cargando: { type: Boolean, default: false },
  conExclusiones: { type: Boolean, default: false },
})
defineEmits(['consultar'])

const NOMBRES_NIVEL = {
  departamento: 'Departamento',
  odei: 'ODEI y encuestador',
  conglomerado: 'Conglomerado',
}
// Mismas opciones que las pantallas actuales: 0 = todos / sin filtro.
const MESES = [
  { title: 'Todos', value: 0 },
  ...['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre',
    'Octubre', 'Noviembre', 'Diciembre'].map((t, i) => ({ title: t, value: i + 1 })),
]
const PERIODOS = [
  { title: 'Todos', value: 0 },
  ...[1, 2, 3, 4, 5].map((p) => ({ title: `Periodo ${p}`, value: p })),
]
const EXCLUSIONES = [
  { title: 'Sin exclusiones', value: 0 },
  { title: 'Excluir no panel', value: 1 },
  { title: 'Excluir panel', value: 2 },
  { title: 'Excluir panel ausente sin teléfono', value: 3 },
]

const odeis = ref([])
const opcionesNivel = computed(() => props.niveles.map((n) => ({ title: NOMBRES_NIVEL[n] ?? n, value: n })))
const requiereOdei = computed(() => filtros.value.nivel !== 'departamento')

onMounted(async () => {
  const { data } = await catalogos.odeis()
  odeis.value = data.map((o) => ({ title: o.nombre, value: o.codigo }))
  if (odeis.value.length === 1) filtros.value.odei = odeis.value[0].value
})
</script>

<template>
  <v-card class="mb-4">
    <v-card-text>
      <v-row dense>
        <v-col cols="12" md="2">
          <v-select v-model="filtros.nivel" :items="opcionesNivel" label="Nivel de detalle" />
        </v-col>
        <v-col cols="6" md="2">
          <v-select v-model="filtros.mes_inicio" :items="MESES" label="Mes inicial" />
        </v-col>
        <v-col cols="6" md="2">
          <v-select v-model="filtros.periodo_inicio" :items="PERIODOS" label="Periodo inicial" />
        </v-col>
        <v-col cols="6" md="2">
          <v-select v-model="filtros.mes_fin" :items="MESES" label="Mes final" />
        </v-col>
        <v-col cols="6" md="2">
          <v-select v-model="filtros.periodo_fin" :items="PERIODOS" label="Periodo final" />
        </v-col>
        <v-col v-if="conExclusiones" cols="12" md="2">
          <v-select v-model="filtros.excluir" :items="EXCLUSIONES" label="Exclusiones" />
        </v-col>
      </v-row>
      <v-row v-if="requiereOdei" dense>
        <v-col cols="12" md="3">
          <v-autocomplete v-model="filtros.odei" :items="odeis" label="ODEI" clearable />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field v-model="filtros.encuestador" label="Encuestador (usuario o DNI)" clearable />
        </v-col>
        <v-col v-if="filtros.nivel === 'conglomerado'" cols="12" md="3">
          <v-text-field v-model="filtros.conglomerado" label="Conglomerado (6 dígitos)" clearable />
        </v-col>
        <v-col v-if="filtros.nivel === 'conglomerado'" cols="12" md="3">
          <v-switch v-model="filtros.solo_activos" label="Solo personal activo" color="primary" hide-details />
        </v-col>
      </v-row>
    </v-card-text>
    <v-card-actions class="px-4 pb-4">
      <v-btn
        color="primary"
        variant="flat"
        prepend-icon="mdi-magnify"
        :loading="cargando"
        :disabled="requiereOdei && !filtros.odei"
        @click="$emit('consultar')"
      >
        Consultar
      </v-btn>
      <slot name="acciones" />
    </v-card-actions>
  </v-card>
</template>
