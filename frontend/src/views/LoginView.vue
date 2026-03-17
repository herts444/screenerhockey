<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">Hockey Screener</h1>
      <h2 class="auth-subtitle">Вход</h2>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>Email</label>
          <input
            v-model="email"
            type="email"
            placeholder="email@example.com"
            required
            autocomplete="email"
          />
        </div>
        <div class="form-group">
          <label>Пароль</label>
          <input
            v-model="password"
            type="password"
            placeholder="Минимум 6 символов"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="error" class="auth-error">{{ error }}</div>

        <button type="submit" class="auth-btn" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <p class="auth-link">
        Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import { useAuth } from '../composables/useAuth'
import { useRouter } from 'vue-router'

export default {
  name: 'LoginView',
  data() {
    return {
      email: '',
      password: '',
      error: '',
      loading: false
    }
  },
  setup() {
    const auth = useAuth()
    const router = useRouter()
    return { auth, router }
  },
  methods: {
    async handleLogin() {
      this.error = ''
      this.loading = true
      try {
        await this.auth.login(this.email, this.password)
        const user = this.auth.state.user
        if (user.role === 'pending') {
          this.router.push('/no-access')
        } else {
          this.router.push('/')
        }
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка входа'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0a0e17;
  padding: 20px;
}

.auth-card {
  background: #141925;
  border: 1px solid #1e2736;
  border-radius: 12px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.auth-title {
  color: #4fc3f7;
  font-size: 24px;
  text-align: center;
  margin: 0 0 4px;
}

.auth-subtitle {
  color: #8899aa;
  font-size: 16px;
  font-weight: 400;
  text-align: center;
  margin: 0 0 28px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  color: #8899aa;
  font-size: 13px;
}

.form-group input {
  background: #0d1117;
  border: 1px solid #1e2736;
  border-radius: 8px;
  padding: 10px 14px;
  color: #e0e0e0;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: #4fc3f7;
}

.auth-error {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #f44336;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.auth-btn {
  background: #4fc3f7;
  color: #0a0e17;
  border: none;
  border-radius: 8px;
  padding: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.auth-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.auth-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auth-link {
  text-align: center;
  margin-top: 20px;
  color: #8899aa;
  font-size: 14px;
}

.auth-link a {
  color: #4fc3f7;
  text-decoration: none;
}

.auth-link a:hover {
  text-decoration: underline;
}
</style>
