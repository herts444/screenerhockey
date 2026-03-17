<template>
  <div class="no-access-page">
    <div class="no-access-card">
      <div class="no-access-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
      </div>
      <h1>У вас нету доступа</h1>
      <p>Ваш аккаунт ожидает подтверждения администратором.<br>Обратитесь к администратору для получения доступа.</p>
      <button class="logout-btn" @click="handleLogout">Выйти</button>
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
  background: #0a0e17;
  padding: 20px;
}

.no-access-card {
  background: #141925;
  border: 1px solid #1e2736;
  border-radius: 12px;
  padding: 48px 40px;
  max-width: 440px;
  text-align: center;
}

.no-access-icon {
  color: #f4a623;
  margin-bottom: 20px;
}

.no-access-card h1 {
  color: #e0e0e0;
  font-size: 22px;
  margin: 0 0 12px;
}

.no-access-card p {
  color: #8899aa;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 28px;
}

.logout-btn {
  background: transparent;
  border: 1px solid #1e2736;
  color: #8899aa;
  padding: 10px 28px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.logout-btn:hover {
  border-color: #4fc3f7;
  color: #4fc3f7;
}
</style>
