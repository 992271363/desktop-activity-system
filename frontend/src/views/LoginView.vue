<template>
  <!-- 1. 这个 div 的 class 是 'auth-page'。所以 CSS 里要用 .auth-page 来设置背景图 -->
  <div class="auth-page">
    <!-- 2. 这个 div 的 class 是 'auth-container'。所以 CSS 里要用 .auth-container 来设置毛玻璃效果 -->
    <div class="auth-container">
      <!-- 这是你的表单内容，它会被包裹在毛玻璃卡片里 -->
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
  // 我看你的路由配置是 '/' 代表 MainView，所以这里用 '/'
  router.push('/')
}
</script>

<!-- ==================== 👇👇👇 关键改动在这里 👇👇👇 ==================== -->
<style scoped>
/* 
  之前是 .background-container，现在我们把它应用到你的 .auth-page 上
*/
.auth-page {
  /* 关键：使用 @ 别名来引用图片 */
  background-image: url('@/assets/images/io_smile.jpg');
  background-size: cover;
  background-position: center;
  min-height: 100vh;
  width: 100%;

  /* 使用 Flexbox 将登录框居中 */
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 
  之前是 .frosted-glass-overlay，现在我们把它应用到你的 .auth-container 上
*/
.auth-container {
  /* 应用背景模糊滤镜 */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);

  /* 设置半透明背景 */
  background-color: rgba(255, 255, 255, 0.2);

  /* 其他美化样式 */
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);

  /* 限制最大宽度，并给内部内容一些空间 */
  max-width: 420px; /* 登录框通常窄一些 */
  width: 90%;
  padding: 40px;
  box-sizing: border-box; /* 确保 padding 不会撑大宽度 */
}

/* 
  为了确保在毛玻璃上的内容清晰可读，
  我们可以统一给表单部分的文字加一点阴影或者设置深色。
  这里我们直接使用你已有的 .form-section。
*/
.form-section {
  color: #333; /* 确保文字颜色足够深 */
  text-align: center;
}

/* --- 下面是你已有的表单样式，我帮你整合并美化了一下 --- */

.form-section h1 {
  margin: 0 0 10px;
  font-size: 24px;
}

.subtitle {
  margin-bottom: 30px;
  color: #555;
}

.form-group {
  margin-bottom: 20px;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-sizing: border-box; /* 关键 */
}

.form-actions {
  text-align: right;
  margin-bottom: 20px;
}

.forgot-password {
  font-size: 14px;
  color: #007bff;
  text-decoration: none;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background-color: #007bff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.submit-btn:hover {
  background-color: #0056b3;
}

.switch-auth {
  margin-top: 25px;
}
</style>
