<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="form-section">
        <h1>创建您的账户</h1>
        <p class="subtitle">加入我们，开启全新体验</p>

        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label for="reg-username">用户名</label>
            <input
              id="reg-username"
              type="text"
              v-model="registerData.username"
              placeholder="设置您的用户名"
              required
            />
          </div>
          <div class="form-group">
            <label for="reg-email">邮箱</label>
            <input
              id="reg-email"
              type="email"
              v-model="registerData.email"
              placeholder="请输入您的邮箱"
              required
            />
          </div>
          <div class="form-group">
            <label for="reg-password">密码</label>
            <input
              id="reg-password"
              type="password"
              v-model="registerData.password"
              placeholder="至少8位，包含字母和数字"
              required
            />
          </div>
          <div class="form-group">
            <label for="reg-confirm-password">确认密码</label>
            <input
              id="reg-confirm-password"
              type="password"
              v-model="registerData.confirmPassword"
              placeholder="请再次输入密码"
              required
            />
          </div>
          <button type="submit" class="submit-btn">立 即 注 册</button>
        </form>

        <div class="switch-auth">
          <p>已有账号？ <router-link to="/login">返回登录</router-link></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const registerData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})
const handleRegister = () => {
  if (registerData.password !== registerData.confirmPassword) {
    alert('两次输入的密码不一致！')
    return
  }
  console.log('正在使用以下信息注册:', registerData)

  // 假设 API 调用成功
  // registerApi(registerData).then(() => {
  alert('注册成功！将跳转到登录页面。')
  // **改动在这里：取消了下面这行的注释，激活了跳转功能！**
  router.push('/login')

  // });
}
</script>
