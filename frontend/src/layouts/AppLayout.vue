<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { MENU, menuPara, rutaModulo } from '@/config/menu'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const drawer = ref(true)
const menu = computed(() => menuPara(auth.modulos))

const enConstruccion = (m, p) => !p.migrada && !(p.indicador && m.modulo === 'cobertura')

// Abre en el menú el módulo y el submenú de la pantalla actual
const abiertos = ref([])
watch(
  () => route.meta.pantalla,
  (pantalla) => {
    if (!pantalla) return
    const [modulo, slug] = pantalla.split('/')
    const m = MENU.find((x) => x.modulo === modulo)
    const grupo = m?.pantallas.find((p) => p.grupo && p.pantallas.some((h) => h.slug === slug))
    abiertos.value = [...new Set([...abiertos.value, modulo, ...(grupo ? [`${modulo}/${grupo.grupo}`] : [])])]
  },
  { immediate: true },
)

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
    <v-list v-model:opened="abiertos" class="menu" density="compact" nav>
      <v-list-item :to="{ name: 'inicio' }" prepend-icon="mdi-home-outline" title="Inicio" exact />
      <v-list-group v-for="m in menu" :key="m.modulo" :value="m.modulo">
        <template #activator="{ props }">
          <v-list-item v-bind="props" :prepend-icon="m.icono" :title="m.titulo" />
        </template>
        <template v-for="p in m.pantallas" :key="p.slug ?? p.grupo">
          <!-- Submenú (p. ej. "Tasa de no respuesta"), igual que en el sistema actual -->
          <v-list-group v-if="p.grupo" :value="`${m.modulo}/${p.grupo}`">
            <template #activator="{ props }">
              <v-list-item v-bind="props" :title="p.grupo" density="compact" />
            </template>
            <v-list-item
              v-for="h in p.pantallas"
              :key="h.slug"
              :to="`${rutaModulo(m.modulo)}/${h.slug}`"
              :title="h.titulo"
              density="compact"
            >
              <template v-if="enConstruccion(m, h)" #append>
                <v-icon size="x-small" icon="mdi-progress-wrench" title="En construcción" />
              </template>
            </v-list-item>
          </v-list-group>
          <v-list-item
            v-else
            :to="`${rutaModulo(m.modulo)}/${p.slug}`"
            :title="p.titulo"
            density="compact"
          >
            <template v-if="enConstruccion(m, p)" #append>
              <v-icon size="x-small" icon="mdi-progress-wrench" title="En construcción" />
            </template>
          </v-list-item>
        </template>
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
/* Títulos largos en varias líneas, como en el sistema actual (sin cortar con "...") */
.menu :deep(.v-list-item-title) { white-space: normal; hyphens: none; line-height: 1.3; }
.titulo-sistema { font-size: 1.25rem; font-weight: 500; letter-spacing: 0.01em; }
</style>
