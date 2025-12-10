<template>
  <div class="not-found-container">
    <!-- 增加这层 glass-card 用来承载毛玻璃效果 -->
    <div class="glass-card">
      <div class="content">
        <h1>404</h1>
        <p>抱歉，你访问的页面似乎飞到了外太空。</p>
        <button @click="$router.push('/')" class="back-btn">返回首页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>

.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh; 
  width: 100%;
}

.glass-card {
  background: rgba(30, 35, 50, 0.55);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px; 
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  
  padding: 3rem 4rem; 
  text-align: center;
  transition: transform 0.3s ease;
}

.glass-card:hover {
  transform: translateY(-5px); 
}

h1 {
  font-size: 6rem;
  margin: 0;
  line-height: 1;
  color: #4299e1; 
  font-weight: 700;
  text-shadow: 0 4px 10px rgba(66, 153, 225, 0.3); 
}

p {
  font-size: 1.2rem;
  margin: 1.5rem 0 2.5rem;
  color: #a0aec0; 
}

.back-btn {
  padding: 0.8rem 2.5rem;
  background-color: #4299e1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.back-btn:hover {
  background-color: #3182ce;
  transform: scale(1.05); 
}

.back-btn:active {
  transform: scale(0.95);
}
</style>