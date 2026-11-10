<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { mensajeError } from '@/api/http'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const usuario = ref('')
const password = ref('')
const verPassword = ref(false)
const cargando = ref(false)
const error = ref('')

async function ingresar() {
  error.value = ''
  cargando.value = true
  try {
    await auth.login(usuario.value.trim(), password.value)
    const siguiente = route.query.siguiente
    router.push(typeof siguiente === 'string' && siguiente.startsWith('/') ? siguiente : '/')
  } catch (e) {
    error.value = mensajeError(e)
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <v-main class="d-flex align-center justify-center bg-background">
    <v-card width="380" class="pa-6" elevation="2">
      <h1 class="text-h6 mb-1">Monitoreo ENAHO</h1>
      <p class="text-body-2 text-medium-emphasis mb-6">Ingrese con su usuario del sistema.</p>
      <v-form @submit.prevent="ingresar">
        <v-text-field
          v-model="usuario"
          label="Usuario"
          autocomplete="username"
          prepend-inner-icon="mdi-account-outline"
          autofocus
        />
        <v-text-field
          v-model="password"
          label="Contraseña"
          :type="verPassword ? 'text' : 'password'"
          autocomplete="current-password"
          prepend-inner-icon="mdi-lock-outline"
          :append-inner-icon="verPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="verPassword = !verPassword"
        />
        <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-4">
          {{ error }}
        </v-alert>
        <v-btn type="submit" color="primary" block :loading="cargando" :disabled="!usuario || !password">
          Ingresar
        </v-btn>
      </v-form>
    </v-card>
  </v-main>
</template>
