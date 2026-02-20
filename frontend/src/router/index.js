import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
