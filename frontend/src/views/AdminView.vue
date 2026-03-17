<template>
  <div class="home-page">
    <header class="header">
      <AppNav />
    </header>

    <main class="main-content">
      <div class="admin-container">
        <div class="admin-header">
          <h2>Пользователи</h2>
          <span class="user-count" v-if="users.length">{{ users.length }}</span>
        </div>

        <div v-if="loading" class="admin-status">Загрузка...</div>
        <div v-else-if="error" class="admin-status error">{{ error }}</div>

        <table v-else class="admin-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Дата</th>
              <th>Роль</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.email">
              <td class="cell-email">{{ user.email }}</td>
              <td class="cell-date">{{ formatDate(user.created_at) }}</td>
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
    return { users: [], loading: true, error: '' }
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
        alert(e.response?.data?.error || 'Ошибка')
        await this.loadUsers()
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return '—'
      try {
        return new Date(dateStr).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
      } catch { return dateStr }
    }
  }
}
</script>

<style scoped>
.admin-container {
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 16px;
}

.admin-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.admin-header h2 {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0;
}

.user-count {
  background: var(--bg-tertiary);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border: 1px solid var(--border-color);
}

.admin-status {
  color: var(--text-muted);
  font-size: 14px;
  padding: 40px 0;
  text-align: center;
}

.admin-status.error {
  color: var(--accent-red);
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
}

.admin-table th {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.admin-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
}

.cell-email {
  color: var(--text-primary);
  font-size: 13px;
}

.cell-date {
  color: var(--text-muted);
  font-size: 13px;
}

.role-select {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 5px 8px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.role-select:hover {
  border-color: var(--text-muted);
}

.role-select.role-admin {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.role-select.role-approved {
  color: var(--accent-green);
  border-color: rgba(16, 185, 129, 0.3);
}

.role-select.role-pending {
  color: var(--accent-yellow);
  border-color: rgba(245, 158, 11, 0.3);
}
</style>
