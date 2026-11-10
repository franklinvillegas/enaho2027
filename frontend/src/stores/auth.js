import { defineStore } from 'pinia'
import { auth } from '@/api/comun'

export const useAuthStore = defineStore('auth', {
  state: () => ({ usuario: null, cargado: false }),
  getters: {
    autenticado: (s) => !!s.usuario,
    modulos: (s) => s.usuario?.modulos ?? [],
    puedeVer: (s) => (modulo) => (s.usuario?.modulos ?? []).includes(modulo),
  },
  actions: {
    async cargar() {
      try {
        const { data } = await auth.yo()
        this.usuario = data
      } catch {
        this.usuario = null
      } finally {
        this.cargado = true
      }
    },
    async login(usuario, password) {
      await auth.csrf()
      const { data } = await auth.login(usuario, password)
      this.usuario = data
    },
    async logout() {
      try {
        await auth.logout()
      } finally {
        this.usuario = null
      }
    },
  },
})
