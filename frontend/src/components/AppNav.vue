<template>
  <div class="header-row header-row-main">
    <div class="header-brand">
      <router-link to="/" class="logo">
        <span class="logo-text">Hockey Screener</span>
      </router-link>
      <nav class="main-nav">
        <router-link
          to="/"
          :class="['nav-btn', { active: $route.path === '/' }]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3v18h18"/>
            <path d="m19 9-5 5-4-4-3 3"/>
          </svg>
          Статистика
        </router-link>
        <router-link
          to="/value-bets"
          :class="['nav-btn', 'nav-btn-value', { active: $route.path === '/value-bets' }]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          Value Bets
        </router-link>
        <router-link
          to="/lineups"
          :class="['nav-btn', 'nav-btn-lineups', { active: $route.path === '/lineups' }]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          Составы
        </router-link>
        <router-link
          v-if="isAdmin"
          to="/admin"
          :class="['nav-btn', 'nav-btn-admin', { active: $route.path === '/admin' }]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          Админ
        </router-link>
      </nav>
    </div>
    <div class="header-user">
      <span class="user-email">{{ userEmail }}</span>
      <button class="logout-btn" @click="handleLogout">Выйти</button>
    </div>
  </div>
</template>

<script>
import { useAuth } from '../composables/useAuth'
import { useRouter } from 'vue-router'

export default {
  name: 'AppNav',
  setup() {
    const auth = useAuth()
    const router = useRouter()

    function handleLogout() {
      auth.logout()
      router.push('/login')
    }

    return {
      isAdmin: auth.isAdmin,
      auth,
      handleLogout
    }
  },
  computed: {
    userEmail() {
      return this.auth.state.user?.email || ''
    }
  }
}
</script>

<style scoped>
.header-row-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-email {
  color: #8899aa;
  font-size: 13px;
}

.logout-btn {
  background: transparent;
  border: 1px solid #1e2736;
  color: #8899aa;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.logout-btn:hover {
  border-color: #f44336;
  color: #f44336;
}

.nav-btn-admin {
  color: #4fc3f7;
}

.nav-btn-admin.active {
  color: #4fc3f7;
  background: rgba(79, 195, 247, 0.1);
}
</style>
