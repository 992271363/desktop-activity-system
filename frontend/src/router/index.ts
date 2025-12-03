import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login', // 定义URL路径
      name: 'login',
      component: LoginView, // 指定对应的组件
    },
    // 你可以把根路径重定向到登录页
    {
      path: '/',
      redirect: '/login',
    },
  ],
})

export default router
