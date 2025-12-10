// frontend/src/utils/request.ts
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api', // 配合 nginx 转发
  timeout: 10000,
})

// 请求拦截器：每次请求都带上 Token
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 响应拦截器：处理 401 token 过期等
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token 过期或未登录，强制登出
      const authStore = useAuthStore()
      authStore.logout()
      // 这里可以加跳转逻辑，或者由组件的 Watcher 处理
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default request
