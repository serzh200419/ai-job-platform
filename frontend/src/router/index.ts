import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../services/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    {
      path: '/login',
      component: () => import('../views/Login.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      component: () => import('../views/Register.vue'),
      meta: { guest: true },
    },
    {
      path: '/dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/jobs',
      component: () => import('../views/Jobs.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/jobs/:id',
      component: () => import('../views/JobDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ai',
      component: () => import('../views/AIAssistant.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    next('/login')
  } else if (to.meta.guest && isAuthenticated()) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
