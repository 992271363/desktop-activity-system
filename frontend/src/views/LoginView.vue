<script setup lang="ts">
// 目前不需要写任何逻辑
</script>

<template>
  <div class="login-container">
    <h1>请登录</h1>
    <form>
      <div>
        <label for="username">用户名:</label>
        <input type="text" id="username" />
      </div>
      <div>
        <label for="password">密码:</label>
        <input type="password" id="password" />
      </div>
      <button type="submit">登录</button>
    </form>
  </div>
</template>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
</style>
