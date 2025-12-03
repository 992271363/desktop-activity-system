<template>
  <div class="main-container">
    <h1>欢迎来到主界面 (MainView)</h1>
    <p>这里是登录成功后才能看到的内容区域。</p>
    <p>你可以开始在这里构建你应用的核心功能了！</p>
    <button @click="handleLogout">退出登录</button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

// 获取路由器实例
const router = useRouter()

// 处理退出登录的函数
const handleLogout = () => {
  // 1. 清除用户的登录状态（例如，从 localStorage 中移除 token）
  // 这只是一个示例，你需要根据你的实际登录逻辑来清除
  localStorage.removeItem('user-token')

  // 2. 提示用户已退出
  alert('您已成功退出登录！')

  // 3. 跳转回登录页面
  router.push('/login')
}
</script>

<style scoped>
.main-container {
  max-width: 600px;
  margin: 50px auto;
  padding: 20px;
  text-align: center;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #f9f9f9;
}

button {
  margin-top: 20px;
  padding: 10px 20px;
  font-size: 16px;
  color: #fff;
  background-color: #dc3545;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background-color: #c82333;
}
</style>
