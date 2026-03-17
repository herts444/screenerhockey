<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h1>HOCKEY SCREENER</h1>
        <p>Регистрация</p>
      </div>

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
          <label>Подтверждение пароля</label>
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

        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Регистрация...' : 'Создать аккаунт' }}
        </button>
      </form>

      <p class="auth-footer">
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
    return { email: '', password: '', confirmPassword: '', error: '', success: '', loading: false }
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
        this.success = data.message || 'Регистрация успешна. Ожидайте подтверждения.'
        if (data.role === 'admin') {
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
  background: var(--bg-primary);
  padding: 20px;
}

.auth-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 48px 40px;
  width: 100%;
  max-width: 380px;
}

.auth-header {
  margin-bottom: 32px;
}

.auth-header h1 {
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
  margin: 0 0 6px;
}

.auth-header p {
  color: var(--text-muted);
  font-size: 13px;
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group input {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  padding: 10px 12px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: var(--text-secondary);
}

.form-group input::placeholder {
  color: var(--text-muted);
}

.auth-error {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: var(--accent-red);
  padding: 10px 12px;
  font-size: 13px;
}

.auth-success {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: var(--accent-green);
  padding: 10px 12px;
  font-size: 13px;
}

.btn-primary {
  background: var(--text-primary);
  color: var(--bg-primary);
  border: none;
  padding: 11px;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.85;
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  color: var(--text-muted);
  font-size: 13px;
}

.auth-footer a {
  color: var(--text-primary);
  text-decoration: none;
  border-bottom: 1px solid var(--border-light);
  transition: border-color 0.2s;
}

.auth-footer a:hover {
  border-color: var(--text-primary);
}
</style>
