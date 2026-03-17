import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
    meta: { public: true }
  },
  {
    path: '/no-access',
    name: 'NoAccess',
    component: () => import('../views/NoAccessView.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Stats',
    component: () => import('../views/StatsView.vue')
  },
  {
    path: '/value-bets',
    name: 'ValueBets',
    component: () => import('../views/ValueBetsView.vue')
  },
  {
    path: '/lineups',
    name: 'Lineups',
    component: () => import('../views/LineupsView.vue')
  },
  {
    path: '/winners',
    name: 'Winners',
    component: () => import('../views/Winners.vue')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/AdminView.vue'),
    meta: { requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuth()

  // Public routes — allow always
  if (to.meta.public) {
    // If already logged in and going to login/register, redirect to home
    if (auth.isLoggedIn.value && (to.name === 'Login' || to.name === 'Register')) {
      return next('/')
    }
    return next()
  }

  // Not logged in — go to login
  if (!auth.isLoggedIn.value) {
    return next('/login')
  }

  // Fetch user from server if not loaded yet
  if (!auth.state.user) {
    await auth.fetchUser()
  }

  // Still no user (token invalid) — go to login
  if (!auth.state.user) {
    return next('/login')
  }

  // Not approved — go to no-access
  if (!auth.isApproved.value) {
    return next('/no-access')
  }

  // Admin-only routes
  if (to.meta.requiresAdmin && !auth.isAdmin.value) {
    return next('/')
  }

  next()
})

export default router
