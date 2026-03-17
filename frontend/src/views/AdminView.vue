<template>
  <div class="home-page">
    <header class="header">
      <AppNav />
    </header>

    <main class="main-content">
      <div class="admin-container">
        <h2 class="admin-title">Управление пользователями</h2>

        <div v-if="loading" class="admin-loading">Загрузка...</div>
        <div v-else-if="error" class="admin-error">{{ error }}</div>

        <table v-else class="admin-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Дата регистрации</th>
              <th>Роль</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.email">
              <td>{{ user.email }}</td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td>
                <select
                  :value="user.role"
                  @change="updateRole(user.email, $event.target.value)"
                  class="role-select"
                  :class="'role-' + user.role"
                >
                  <option value="pending">Ожидает</option>
                  <option value="approved">Одобрен</option>
                  <option value="admin">Админ</option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script>
import AppNav from '../components/AppNav.vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export default {
  name: 'AdminView',
  components: { AppNav },
  data() {
    return {
      users: [],
      loading: true,
      error: ''
    }
  },
  async mounted() {
    await this.loadUsers()
  },
  methods: {
    async loadUsers() {
      this.loading = true
      this.error = ''
      try {
        const res = await axios.get(`${API_BASE}/admin/users`)
        this.users = res.data.users
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка загрузки'
      } finally {
        this.loading = false
      }
    },
    async updateRole(email, role) {
      try {
        await axios.post(`${API_BASE}/admin/users`, { email, role })
        const user = this.users.find(u => u.email === email)
        if (user) user.role = role
      } catch (e) {
        alert(e.response?.data?.error || 'Ошибка обновления роли')
        await this.loadUsers()
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return '-'
      try {
        const d = new Date(dateStr)
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
      } catch {
        return dateStr
      }
    }
  }
}
</script>

<style scoped>
.admin-container {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px 16px;
}

.admin-title {
  color: #e0e0e0;
  font-size: 20px;
  margin: 0 0 20px;
}

.admin-loading,
.admin-error {
  color: #8899aa;
  padding: 40px;
  text-align: center;
}

.admin-error {
  color: #f44336;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  background: #141925;
  border-radius: 8px;
  overflow: hidden;
}

.admin-table th {
  background: #1a2030;
  color: #8899aa;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #1e2736;
}

.admin-table td {
  padding: 12px 16px;
  color: #e0e0e0;
  font-size: 14px;
  border-bottom: 1px solid #1e2736;
}

.role-select {
  background: #0d1117;
  border: 1px solid #1e2736;
  border-radius: 6px;
  padding: 6px 10px;
  color: #e0e0e0;
  font-size: 13px;
  cursor: pointer;
  outline: none;
}

.role-select.role-admin {
  border-color: #4fc3f7;
  color: #4fc3f7;
}

.role-select.role-approved {
  border-color: #4caf50;
  color: #4caf50;
}

.role-select.role-pending {
  border-color: #f4a623;
  color: #f4a623;
}
</style>
