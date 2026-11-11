import { createRouter, createWebHistory } from 'vue-router'
import { MENU, pantallasDe, rutaModulo } from '@/config/menu'
import { useAuthStore } from '@/stores/auth'

import AppLayout from '@/layouts/AppLayout.vue'
import LoginView from '@/views/LoginView.vue'
import InicioView from '@/views/InicioView.vue'

const IndicadorCobertura = () => import('@/views/cobertura/IndicadorCoberturaView.vue')
const TnrTotal = () => import('@/views/cobertura/TnrTotalView.vue')

// Pantallas con vista propia (replican el diseño de la pantalla actual)
const VISTAS_PROPIAS = { 'cobertura/tnr-total': TnrTotal }
const EnConstruccion = () => import('@/views/EnConstruccionView.vue')

// Una ruta por pantalla del menú. Las pantallas migradas apuntan a su vista real.
const rutasPantallas = MENU.flatMap((m) =>
  pantallasDe(m).map((p) => ({
    path: `${rutaModulo(m.modulo)}/${p.slug}`,
    name: `${m.modulo}-${p.slug}`,
    component:
      VISTAS_PROPIAS[`${m.modulo}/${p.slug}`] ??
      (m.modulo === 'cobertura' && p.indicador ? IndicadorCobertura : EnConstruccion),
    props: p.indicador ? { indicador: p.indicador, titulo: p.titulo } : { titulo: p.titulo },
    meta: { modulo: m.modulo, titulo: p.titulo, pantalla: `${m.modulo}/${p.slug}` },
  })),
)

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { publica: true } },
    {
      path: '/',
      component: AppLayout,
      children: [{ path: '', name: 'inicio', component: InicioView }, ...rutasPantallas],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.cargado) await auth.cargar()
  if (to.meta.publica) return auth.autenticado ? { name: 'inicio' } : true
  if (!auth.autenticado) return { name: 'login', query: { siguiente: to.fullPath } }
  if (to.meta.modulo && !auth.puedeVer(to.meta.modulo)) return { name: 'inicio' }
  return true
})

// La sesión venció mientras se usaba la aplicación
window.addEventListener('api:no-autorizado', async () => {
  const auth = useAuthStore()
  await auth.cargar()
  if (!auth.autenticado && router.currentRoute.value.name !== 'login') {
    router.push({ name: 'login', query: { siguiente: router.currentRoute.value.fullPath } })
  }
})

export default router
