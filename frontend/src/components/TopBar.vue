<!-- src/components/TopBar.vue -->
<template>
  <header class="top-bar">
    <div class="top-bar-content">
      <!-- 左侧：Logo 和应用名称 -->
      <div class="logo-area">
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 2L2 7V17L12 22L22 17V7L12 2Z"
            stroke="#4299e1"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M2 7L12 12L22 7"
            stroke="#4299e1"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M12 22V12"
            stroke="#4299e1"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span class="app-name">桌面活动管理系统</span>
      </div>

      <!-- 右侧：操作区 -->
      <div class="actions-area">
        <div class="user-avatar">
          <span>A</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
// 目前不需要脚本逻辑
</script>

<style scoped>
/* 顶栏容器，固定在顶部，全宽，应用毛玻璃效果 */
.top-bar {
  position: fixed; /* 固定在视口顶部 */
  top: 0;
  left: 0;
  width: 100%;
  height: 64px; /* 关键！固定高度，为下方内容区留出空间 */
  z-index: 1000; /* 确保在最上层 */

  /* 核心：毛玻璃背景 */
  background-color: rgba(26, 32, 44, 0.65); /* 半透明深蓝灰色背景 */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1); /* 底部细线，增加质感 */
}

/* 顶栏内容区，限制最大宽度并居中，与仪表盘内容对齐 */
.top-bar-content {
  max-width: 1600px;
  height: 100%;
  margin: 0 auto;
  padding: 0 2rem; /* 两边留出间距，与 MainView 对应 */
  display: flex;
  justify-content: space-between; /* 两端对齐 */
  align-items: center; /* 垂直居中 */
}

/* 左侧 Logo 区域 */
.logo-area {
  display: flex;
  align-items: center;
  gap: 0.75rem; /* 图标和文字的间距 */
}

.app-name {
  font-size: 1.15rem;
  font-weight: 600;
  color: #f7fafc; /* 亮白色 */
}

/* 右侧操作区域 */
.actions-area {
  display: flex;
  align-items: center;
  gap: 1rem;
}

/* 用户头像 */
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #3182ce; /* 蓝色 */
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.5);
  transition: transform 0.2s;
}
.user-avatar:hover {
  transform: scale(1.1);
}
</style>
