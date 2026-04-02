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
import request from '@/utils/request'
import axios, { AxiosError } from 'axios'
import '@/assets/css/auth-styles.css'


interface LoginResponse {
  access_token: string
  token_type: string
  // 后端其他字段，可以在这里补充
}


interface BackendError {
  detail: string
}

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
    const params = new URLSearchParams()
    params.append('username', loginData.username)
    params.append('password', loginData.password)

    // 3. 发起请求并指定返回类型
    // 因为 request.ts 拦截器返回了 response.data，所以这里 res 的类型就是 LoginResponse
    const res = await request.post<LoginResponse>('/auth/token', params) as unknown as LoginResponse

    const { access_token } = res

    authStore.setLoginState(access_token, loginData.username)
    
    console.log('登录成功')
    router.push('/')
  } catch (err: unknown) {
    console.error('登录异常:', err)

    if (axios.isAxiosError(err)) {
      const axiosError = err as AxiosError<BackendError>
      const errorMsg = axiosError.response?.data?.detail || '用户名或密码错误'
      errorMessage.value = errorMsg
    } else {
      errorMessage.value = '网络异常，请稍后再试'
    }
  } finally {
    isLoading.value = false
  }
}
</script>