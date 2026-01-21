import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
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
