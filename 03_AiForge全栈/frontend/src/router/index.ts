import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    guest?: boolean
    requiresAuth?: boolean
    requiresAdmin?: boolean
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/workspace',
    name: 'workspace',
    component: () => import('@/views/Workspace.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/gallery',
    name: 'gallery',
    component: () => import('@/views/Gallery.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/pricing',
    name: 'pricing',
    component: () => import('@/views/Pricing.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/referral',
    name: 'referral',
    component: () => import('@/views/Referral.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/project',
    name: 'project',
    component: () => import('@/views/Project.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/Admin.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/',
    redirect: '/workspace',
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/workspace',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  if (auth.isLoggedIn && !auth.user) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return next({ name: 'login' })
  }

  if (to.meta.guest && auth.isLoggedIn) {
    return next({ name: 'workspace' })
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next({ name: 'workspace' })
  }

  next()
})

export default router
