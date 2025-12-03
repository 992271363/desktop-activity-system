<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="form-section">
        <h1>欢迎回来！</h1>
        <p class="subtitle">登录以继续</p>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="login-username">用户名 / 邮箱</label>
            <input
              id="login-username"
              type="text"
              v-model="loginData.username"
              placeholder="请输入用户名或邮箱"
              required
            />
          </div>
          <div class="form-group">
            <label for="login-password">密码</label>
            <input
              id="login-password"
              type="password"
              v-model="loginData.password"
              placeholder="请输入密码"
              required
            />
          </div>
          <div class="form-actions">
            <a href="#" class="forgot-password">忘记密码?</a>
          </div>
          <button type="submit" class="submit-btn">登 录</button>
        </form>

        <div class="switch-auth">
          <p>还没有账号？ <router-link to="/register">立即注册</router-link></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import '@/assets/css/auth-styles.css'
const router = useRouter()
const loginData = reactive({
  username: '',
  password: '',
})
const handleLogin = () => {
  if (!loginData.username || !loginData.password) {
    alert('请填写完整的登录信息！')
    return
  }
  console.log('正在使用以下信息登录:', loginData)

  // 假设登录成功，我们现在跳转到主界面
  router.push('/')
}
</script>
