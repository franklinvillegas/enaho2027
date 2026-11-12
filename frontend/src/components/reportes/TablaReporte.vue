<script setup>
// Tabla de reporte con el diseño del sistema actual: encabezado azul agrupado (celdas que
// ocupan varias filas o columnas), total en amarillo, filas alternadas, enlaces para bajar
// de nivel, mes del conglomerado en rojo y grupos de columnas que se abren y cierran
// (como "Omisión Total ±" en omisión por capítulos).
//
// modelo = {
//   encabezados: [[{ texto, columnas, columnasCerrado, filas, grupo, alternar }]],
//     (columnasCerrado: ancho de la celda cuando su grupo `alternar` está cerrado)
//   filas: [{ total, celdas: [{ texto, enlace, url, resaltado, izquierda, grupo }] }],
//   fijas: n.º de columnas fijas a la izquierda,
// }
import { computed } from 'vue'

const props = defineProps({
  modelo: { type: Object, required: true },
  cerrados: { type: Object, default: () => new Set() }, // grupos de columnas cerrados
  busqueda: { type: String, default: '' },
  color: { type: String, default: '#0065A9' },
  alto: { type: Number, default: 0 },
})
const emit = defineEmits(['ir', 'alternar'])

const visible = (c) => !c.grupo || !props.cerrados.has(c.grupo)
const encabezados = computed(() => props.modelo.encabezados.map((fila) => fila.filter(visible)))
const filas = computed(() => {
  const t = props.busqueda.trim().toLowerCase()
  return props.modelo.filas
    .map((f, i) => ({ ...f, i, celdas: f.celdas.filter(visible) }))
    .filter((f) => !t || f.total || f.celdas.some((c) => String(c.texto ?? '').toLowerCase().includes(t)))
})
const fijas = computed(() => props.modelo.fijas ?? 0)
const ancho = (c) => (c.alternar && c.columnasCerrado && props.cerrados.has(c.alternar) ? c.columnasCerrado : (c.columnas ?? 1))
</script>

<template>
  <div class="contenedor" :style="alto ? { maxHeight: `${alto}px` } : {}">
    <table class="tabla" :style="{ '--azul': color }">
      <thead>
        <tr v-for="(fila, r) in encabezados" :key="r">
          <th v-for="(c, k) in fila" :key="k" :colspan="ancho(c)" :rowspan="c.filas ?? 1"
            :class="{ fijo: r === 0 && k < fijas, [`f${k}`]: r === 0 && k < fijas }">
            <span v-for="(linea, n) in String(c.texto).split('\n')" :key="n"><br v-if="n">{{ linea }}</span>
            <button v-if="c.alternar" class="alternar" :title="cerrados.has(c.alternar) ? 'Ver años anteriores' : 'Ocultar'"
              @click="emit('alternar', c.alternar)">
              {{ cerrados.has(c.alternar) ? '+' : '−' }}
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="f in filas" :key="f.i" :class="f.total ? 'total' : (f.i % 2 ? 'par' : 'impar')">
          <td v-for="(c, k) in f.celdas" :key="k"
            :class="{ fijo: k < fijas, [`f${k}`]: k < fijas, izquierda: c.izquierda, resaltado: c.resaltado }">
            <a v-if="c.enlace" class="enlace" @click="emit('ir', c.enlace)">{{ c.texto }}</a>
            <a v-else-if="c.url" class="enlace" :href="c.url" target="_blank" rel="noopener noreferrer">{{ c.texto }}</a>
            <template v-else>{{ c.texto }}</template>
          </td>
        </tr>
        <tr v-if="!modelo.filas.length">
          <td :colspan="99" class="sin-datos">Sin resultados para los filtros elegidos.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.contenedor { overflow: auto; border-bottom: 1px solid #333; }
.tabla { border-collapse: separate; border-spacing: 0; font-size: 0.72rem; min-width: 100%; }
.tabla thead { position: sticky; top: 0; z-index: 3; }
.tabla th { background: var(--azul); color: #fff; text-align: center; vertical-align: middle; padding: 9px 7px;
  font-weight: 700; border: 1px solid #ddd; white-space: nowrap; }
.tabla td { padding: 8px 7px; border: 1px solid #e3e3e3; white-space: nowrap; text-align: center; background: #fff; }
.tabla tr.par td { background: #EAEAEA; }
.tabla tr.total td { background: #F5FFBE; font-weight: 700; }
.tabla td.izquierda { text-align: left; }
.tabla td.resaltado { color: #FF2400; font-weight: 700; }
.fijo { position: sticky; z-index: 2; }
th.fijo { z-index: 4; }
.f0 { left: 0; min-width: 48px; }
.f1 { left: 48px; min-width: 170px; }
.enlace { color: #1E88E5; cursor: pointer; text-decoration: none; }
.alternar { margin-left: 6px; background: #fff; color: #11519A; border: none; border-radius: 3px; width: 18px;
  height: 18px; line-height: 16px; font-weight: 700; cursor: pointer; }
.sin-datos { padding: 24px; color: #777; }
</style>
