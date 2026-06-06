import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { post, get } from '@/api'

export interface User {
  id: number
  email: string
  nickname: string
  points: number
  role: string
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('aiforge_token'))
  const user = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userPoints = computed(() => user.value?.points ?? 0)

  async function login(email: string, password: string) {
    const data = await post<{ token: string; user: User }>('/auth/login', { email, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('aiforge_token', data.token)
  }

  async function register(email: string, password: string, nickname: string, refCode: string = '') {
    const params = refCode ? `?ref=${encodeURIComponent(refCode)}` : ''
    const data = await post<{ token: string; user: User }>(`/auth/register${params}`, { email, password, nickname })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('aiforge_token', data.token)
  }

  async function fetchMe() {
    try {
      const data = await get<User>('/auth/me')
      user.value = data
    } catch {
      logout()
    }
  }

  async function fetchProfile() {
    const data = await get<User>('/user/profile')
    user.value = data
  }

  async function fetchPoints() {
    const data = await get<{ points: number }>('/user/points')
    if (user.value) {
      user.value.points = data.points
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('aiforge_token')
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    userPoints,
    login,
    register,
    fetchMe,
    fetchProfile,
    fetchPoints,
    logout,
  }
})
