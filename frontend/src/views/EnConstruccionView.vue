<script setup>
defineProps({ titulo: { type: String, required: true } })
</script>

<template>
  <h1 class="text-h5 mb-4">{{ titulo }}</h1>
  <v-alert type="info" variant="tonal" icon="mdi-progress-wrench">
    Esta pantalla todavía no se migra al sistema nuevo. Mientras tanto, siga usándola en el
    sistema actual.
  </v-alert>
</template>
