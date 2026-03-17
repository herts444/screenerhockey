import { reactive, computed } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const state = reactive({
  token: localStorage.getItem('auth_token') || null,
  user: null,
  loading: false,
})

// Attach token to all axios requests globally
axios.interceptors.request.use((config) => {
  if (state.token) {
    config.headers.Authorization = `Bearer ${state.token}`
  }
  return config
})

// On 401 response, clear auth state
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't clear on login/register endpoints
      const url = error.config?.url || ''
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        state.token = null
        state.user = null
        localStorage.removeItem('auth_token')
      }
    }
    return Promise.reject(error)
  }
)

export function useAuth() {
  const isLoggedIn = computed(() => !!state.token)
  const isApproved = computed(() => {
    const role = state.user?.role
    return role === 'approved' || role === 'admin'
  })
  const isAdmin = computed(() => state.user?.role === 'admin')

  async function login(email, password) {
    const res = await axios.post(`${API_BASE}/auth/login`, { email, password })
    state.token = res.data.token
    state.user = res.data.user
    localStorage.setItem('auth_token', res.data.token)
    return res.data
  }

  async function register(email, password) {
    const res = await axios.post(`${API_BASE}/auth/register`, { email, password })
    return res.data
  }

  async function fetchUser() {
    if (!state.token) return null
    state.loading = true
    try {
      const res = await axios.get(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${state.token}` }
      })
      state.user = res.data
      return res.data
    } catch {
      state.token = null
      state.user = null
      localStorage.removeItem('auth_token')
      return null
    } finally {
      state.loading = false
    }
  }

  function logout() {
    state.token = null
    state.user = null
    localStorage.removeItem('auth_token')
  }

  return {
    state,
    isLoggedIn,
    isApproved,
    isAdmin,
    login,
    register,
    fetchUser,
    logout,
  }
}
