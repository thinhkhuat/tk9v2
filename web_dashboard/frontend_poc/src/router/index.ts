import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

// Route definitions
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: {
      title: 'Deep Research Dashboard',
      requiresAuth: true
    }
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: () => import('../views/SessionsDashboard.vue'),
    meta: {
      title: 'Session Management',
      requiresAuth: true
    }
  },
  {
    path: '/sessions/:id',
    name: 'SessionDetail',
    component: () => import('../views/HomeView.vue'),
    meta: {
      title: 'Session Details',
      requiresAuth: true
    }
  },
  {
    // 404 catch-all route
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue'),
    meta: {
      title: 'Page Not Found'
    }
  }
]

// Create router instance
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Authentication & page title navigation guards
router.beforeEach(async (to, _from, next) => {
  // Set page title from route meta
  const title = to.meta.title as string || 'Deep Research Dashboard'
  document.title = title

  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    const authStore = useAuthStore()

    // Wait for auth to be ready if still initializing
    if (authStore.isInitializing) {
      console.log('[Router] Waiting for auth to complete...')
      // Poll until auth is ready (max 5 seconds)
      let attempts = 0
      while (authStore.isInitializing && attempts < 50) {
        await new Promise(resolve => setTimeout(resolve, 100))
        attempts++
      }
    }

    // Check if user is authenticated
    if (!authStore.isAuthenticated) {
      console.warn('[Router] User not authenticated, redirecting to home')
      // For now, allow navigation but log warning
      // In future, could redirect to login page
      next()
    } else {
      console.log('[Router] User authenticated, allowing navigation')
      next()
    }
  } else {
    next()
  }
})

export default router
