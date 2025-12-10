<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="form-section">
        <h1>欢迎回来！</h1>
        <p class="subtitle">登录以继续</p>
        <form @submit.prevent="handleLogin">
          <p v-if="errorMessage" style="color: red; margin-bottom: 10px">{{ errorMessage }}</p>

          <div class="form-group">
            <label for="login-username">用户名</label>
            <input id="login-username" type="text" v-model="loginData.username" required />
          </div>
          <div class="form-group">
            <label for="login-password">密码</label>
            <input id="login-password" type="password" v-model="loginData.password" required />
          </div>

          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '登录中...' : '登 录' }}
          </button>
        </form>
        <!-- 底部 ... -->
        <div class="switch-auth">
          <p>还没有账号？ <router-link to="/register">立即注册</router-link></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios, { AxiosError } from 'axios' // <--- 1. 引入 AxiosError 类型
import '@/assets/css/auth-styles.css'

const router = useRouter()
const authStore = useAuthStore()

const loginData = reactive({
  username: '',
  password: '',
})
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  if (!loginData.username || !loginData.password) {
    errorMessage.value = '请填写完整的登录信息！'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('username', loginData.username)
    formData.append('password', loginData.password)

    const response = await axios.post<{ access_token: string }>('/api/auth/token', formData)

    const { access_token } = response.data

    authStore.setLoginState(access_token, loginData.username)
    router.push('/')
  } catch (err) {
    console.error('登录失败:', err)

    // 3. 使用类型断言，将 err 视为 AxiosError
    const error = err as AxiosError

    if (error.response && error.response.status === 401) {
      errorMessage.value = '用户名或密码错误'
    } else {
      errorMessage.value = '登录失败，请检查网络或稍后重试'
    }
  } finally {
    isLoading.value = false
  }
}
</script>
