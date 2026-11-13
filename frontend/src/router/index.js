import { createRouter, createWebHistory } from 'vue-router'
import { MENU, pantallasDe, rutaModulo } from '@/config/menu'
import { useAuthStore } from '@/stores/auth'

import AppLayout from '@/layouts/AppLayout.vue'
import LoginView from '@/views/LoginView.vue'
import InicioView from '@/views/InicioView.vue'

const Reporte = () => import('@/views/reportes/ReporteView.vue')
const IndicadorCobertura = () => import('@/views/cobertura/IndicadorCoberturaView.vue')
const TasaNoRespuesta = () => import('@/views/cobertura/TasaNoRespuestaView.vue')

// Pantallas con vista propia (replican el diseño de la pantalla actual).
// Las tasas de no respuesta comparten una vista: cambia solo el indicador.
const VISTAS_PROPIAS = {
  'cobertura/tnr-total': { component: TasaNoRespuesta, props: { indicador: 'tnr-total' } },
  'cobertura/tnr-parcial': { component: TasaNoRespuesta, props: { indicador: 'tnr-parcial' } },
  'cobertura/problemas-marco': { component: TasaNoRespuesta, props: { indicador: 'problemas-marco' } },
  'cobertura/informacion-indirecta': { component: TasaNoRespuesta, props: { indicador: 'informacion-indirecta' } },
  // TNR según estrato tiene otra estructura (cuatro pestañas): vista propia
  'cobertura/tnr-estrato': { component: () => import('@/views/cobertura/TnrEstratoView.vue') },
  // Reportes con tablas agrupadas: una vista genérica guiada por config/reportesCobertura
  // y config/reportesCalidad
  ...Object.fromEntries(['control-visitas', 'omision-capitulos', 'omisiones-gps', 'tipo-entrevista'].map((p) => [
    `cobertura/${p}`, { component: Reporte, props: { modulo: 'cobertura', pantalla: p } }])),
  ...Object.fromEntries(['vivienda-hogar', 'programas-sociales'].map((p) => [
    `calidad/${p}`, { component: Reporte, props: { modulo: 'calidad', pantalla: p } }])),
}
const EnConstruccion = () => import('@/views/EnConstruccionView.vue')

// Una ruta por pantalla del menú. Las pantallas migradas apuntan a su vista real.
const rutasPantallas = MENU.flatMap((m) =>
  pantallasDe(m).map((p) => ({
    path: `${rutaModulo(m.modulo)}/${p.slug}`,
    name: `${m.modulo}-${p.slug}`,
    component:
      VISTAS_PROPIAS[`${m.modulo}/${p.slug}`]?.component ??
      (m.modulo === 'cobertura' && p.indicador ? IndicadorCobertura : EnConstruccion),
    props: {
      titulo: p.titulo,
      ...(p.indicador ? { indicador: p.indicador } : {}),
      ...VISTAS_PROPIAS[`${m.modulo}/${p.slug}`]?.props,
    },
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
