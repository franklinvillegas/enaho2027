<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { menuPara, rutaModulo } from '@/config/menu'

const auth = useAuthStore()
const modulos = computed(() => menuPara(auth.modulos))
</script>

<template>
  <h1 class="text-h5 mb-1">Bienvenido(a), {{ auth.usuario?.nombre }}</h1>
  <p class="text-body-2 text-medium-emphasis mb-6">Seleccione un módulo para comenzar.</p>
  <v-row>
    <v-col v-for="m in modulos" :key="m.modulo" cols="12" sm="6" lg="4">
      <v-card :prepend-icon="m.icono" :title="m.titulo" :subtitle="`${m.pantallas.length} pantallas`">
        <v-card-text>
          <v-chip
            v-for="p in m.pantallas.slice(0, 3)"
            :key="p.slug"
            :to="`${rutaModulo(m.modulo)}/${p.slug}`"
            size="small"
            class="mr-1 mb-1"
          >
            {{ p.titulo }}
          </v-chip>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
