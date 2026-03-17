<template>
  <div class="no-access-page">
    <div class="no-access-card">
      <div class="lock-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="0" ry="0"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
      </div>
      <h1>Доступ ограничен</h1>
      <p>Ваш аккаунт ожидает подтверждения администратором.</p>
      <button class="btn-secondary" @click="handleLogout">Выйти</button>
    </div>
  </div>
</template>

<script>
import { useAuth } from '../composables/useAuth'
import { useRouter } from 'vue-router'

export default {
  name: 'NoAccessView',
  setup() {
    const auth = useAuth()
    const router = useRouter()
    function handleLogout() {
      auth.logout()
      router.push('/login')
    }
    return { handleLogout }
  }
}
</script>

<style scoped>
.no-access-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: 20px;
}

.no-access-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 48px 40px;
  max-width: 400px;
  text-align: center;
}

.lock-icon {
  color: var(--text-muted);
  margin-bottom: 24px;
}

.no-access-card h1 {
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin: 0 0 12px;
}

.no-access-card p {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 32px;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 9px 32px;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  border-color: var(--text-secondary);
  color: var(--text-primary);
}
</style>
