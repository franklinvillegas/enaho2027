<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { menuPara, rutaModulo } from '@/config/menu'

const auth = useAuthStore()
const router = useRouter()
const drawer = ref(true)
const menu = computed(() => menuPara(auth.modulos))

async function salir() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <v-app-bar color="#1565C0" density="comfortable" flat>
    <v-app-bar-nav-icon aria-label="Mostrar u ocultar menú" @click="drawer = !drawer" />
    <v-app-bar-title class="text-center titulo-sistema">ENCUESTA NACIONAL DE HOGARES</v-app-bar-title>
    <template #append>
      <span class="text-body-2 mr-3 d-none d-sm-inline font-weight-medium">{{ auth.usuario?.nombre?.toUpperCase() }}</span>
      <v-btn variant="text" prepend-icon="mdi-logout" @click="salir">Salir</v-btn>
    </template>
  </v-app-bar>

  <v-navigation-drawer v-model="drawer" width="300">
    <v-list density="compact" nav>
      <v-list-item :to="{ name: 'inicio' }" prepend-icon="mdi-home-outline" title="Inicio" exact />
      <v-list-group v-for="m in menu" :key="m.modulo" :value="m.modulo">
        <template #activator="{ props }">
          <v-list-item v-bind="props" :prepend-icon="m.icono" :title="m.titulo" />
        </template>
        <v-list-item
          v-for="p in m.pantallas"
          :key="p.slug"
          :to="`${rutaModulo(m.modulo)}/${p.slug}`"
          :title="p.titulo"
          density="compact"
        >
          <template v-if="!p.migrada && !(p.indicador && m.modulo === 'cobertura')" #append>
            <v-icon size="x-small" icon="mdi-progress-wrench" title="En construcción" />
          </template>
        </v-list-item>
      </v-list-group>
    </v-list>
  </v-navigation-drawer>

  <v-main class="bg-white">
    <v-container fluid class="pa-4">
      <router-view />
    </v-container>
  </v-main>
</template>

<style scoped>
.titulo-sistema { font-size: 1.25rem; font-weight: 500; letter-spacing: 0.01em; }
</style>
