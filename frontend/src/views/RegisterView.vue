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
<style scoped>
/*
  背景层样式 - 无需改动
*/
.auth-page {
  background-image: url('@/assets/images/BG.jpg');
  background-size: cover;
  background-position: center;
  min-height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: background-image 0.5s ease-in-out;
}

/*
  毛玻璃容器样式
*/
.auth-container {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);

  /* 🎨 专业建议 #1: 暗色系毛玻璃 */
  /* 对于深色背景，使用半透明的黑色或深色玻璃效果通常比白色更好。 */
  /* 将原来的 rgba(255, 255, 255, 0.2) 改为黑色，并可以适当降低透明度。 */
  background-color: rgba(0, 0, 0, 0.25);

  border-radius: 16px;
  /* 边框也改为半透明的白色，在暗色玻璃上更突出 */
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  max-width: 420px;
  width: 90%;
  padding: 40px;
  box-sizing: border-box;
}

/*
  表单内容区域
*/
.form-section {
  /* ✅ 已修改：将默认文字颜色从深灰改为淡白色 */
  color: #f0f0f0;
  text-align: center;

  /* 🎨 专业建议 #2: 文字阴影 */
  /* 给所有文字添加一点细微的阴影，可以极大地提升在复杂背景下的可读性。*/
  text-shadow: 0px 1px 4px rgba(0, 0, 0, 0.5);
}

/*
  主标题 H1
*/
.form-section h1 {
  margin: 0 0 10px;
  font-size: 24px;
  /* H1 可以使用更亮的纯白色来突出 */
  color: #ffffff;
}

/*
  副标题
*/
.subtitle {
  margin-bottom: 30px;
  /* ✅ 已修改：将中灰色改为与主色调一致的淡白色 */
  color: #f0f0f0;
}

/*
  表单组
*/
.form-group {
  margin-bottom: 20px;
  text-align: left;
}

/*
  标签 Label
*/
.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  /* 它会继承 .form-section 的颜色，这里无需改动 */
}

/*
  输入框 Input
*/
.form-group input {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  box-sizing: border-box;

  /* 🎨 专业建议 #3: 输入框透明化 */
  /* 让输入框也融入背景，而不是突兀的白色。 */
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);

  /* ✅ 已修改：输入框里的文字也要是白色！ */
  color: #ffffff;
  font-weight: 500;
}

/* 输入框 Placeholder 占位符文字颜色 */
.form-group input::placeholder {
  color: #cccccc;
}

/*
  表单操作区域
*/
.form-actions {
  text-align: right;
  margin-bottom: 20px;
}

/*
  “忘记密码”链接
*/
.forgot-password {
  font-size: 14px;
  /* ✅ 已修改：蓝色太暗，换成一个更明亮的颜色 */
  color: #87cefa; /* 淡天蓝色，比纯白更有层次感 */
  text-decoration: none;
  transition: color 0.3s;
}

.forgot-password:hover {
  color: #ffffff;
}

/*
  登录按钮
*/
.submit-btn {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #fff; /* 按钮文字是白色，无需改动 */
  background-color: #007bff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.submit-btn:hover {
  background-color: #0056b3;
}

/*
  切换注册/登录的区域
*/
.switch-auth {
  margin-top: 25px;
}

/* 确保 .switch-auth 里的链接也和“忘记密码”颜色协调 */
.switch-auth a {
  color: #87cefa;
  text-decoration: none;
  font-weight: 600;
}

.switch-auth a:hover {
  color: #ffffff;
}
</style>
