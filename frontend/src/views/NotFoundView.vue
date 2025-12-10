<template>
  <div class="not-found-container">
    <div class="content">
      <h1>404</h1>
      <p>抱歉，你访问的页面不存在。</p>
      <button @click="$router.push('/')" class="back-btn">返回首页</button>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60vh; /* 占据一定高度 */
  text-align: center;
  color: #e2e8f0;
}

h1 {
  font-size: 6rem;
  margin: 0;
  color: #4299e1;
}

p {
  font-size: 1.5rem;
  margin-bottom: 2rem;
  color: #a0aec0;
}

.back-btn {
  padding: 0.75rem 2rem;
  background-color: #4299e1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s;
}

.back-btn:hover {
  background-color: #3182ce;
}
</style>