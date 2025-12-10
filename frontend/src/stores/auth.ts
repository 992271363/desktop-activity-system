// frontend/src/stores/auth.ts
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  // 从 localStorage 初始化 token，实现刷新不丢失
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const username = ref<string | null>(localStorage.getItem('username'))

  const isAuthenticated = computed(() => !!token.value)

  function setLoginState(newToken: string, newUsername: string) {
    token.value = newToken
    username.value = newUsername
    localStorage.setItem('access_token', newToken)
    localStorage.setItem('username', newUsername)
  }

  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
  }

  return { token, username, isAuthenticated, setLoginState, logout }
})
