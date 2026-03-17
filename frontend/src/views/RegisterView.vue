<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">Hockey Screener</h1>
      <h2 class="auth-subtitle">Регистрация</h2>

      <form @submit.prevent="handleRegister" class="auth-form">
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
            autocomplete="new-password"
          />
        </div>
        <div class="form-group">
          <label>Подтвердите пароль</label>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="Повторите пароль"
            required
            autocomplete="new-password"
          />
        </div>

        <div v-if="error" class="auth-error">{{ error }}</div>
        <div v-if="success" class="auth-success">{{ success }}</div>

        <button type="submit" class="auth-btn" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p class="auth-link">
        Уже есть аккаунт? <router-link to="/login">Войти</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import { useAuth } from '../composables/useAuth'
import { useRouter } from 'vue-router'

export default {
  name: 'RegisterView',
  data() {
    return {
      email: '',
      password: '',
      confirmPassword: '',
      error: '',
      success: '',
      loading: false
    }
  },
  setup() {
    const auth = useAuth()
    const router = useRouter()
    return { auth, router }
  },
  methods: {
    async handleRegister() {
      this.error = ''
      this.success = ''

      if (this.password !== this.confirmPassword) {
        this.error = 'Пароли не совпадают'
        return
      }

      this.loading = true
      try {
        const data = await this.auth.register(this.email, this.password)
        this.success = data.message || 'Регистрация успешна. Ожидайте подтверждения администратора.'

        if (data.role === 'admin') {
          // First user — auto login
          await this.auth.login(this.email, this.password)
          this.router.push('/')
        } else {
          setTimeout(() => this.router.push('/login'), 2000)
        }
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка регистрации'
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

.auth-success {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
  color: #4caf50;
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
