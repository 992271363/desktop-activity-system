import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'main',
      component: () => import('@/views/MainView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { hideTopBar: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { hideTopBar: true }
    },
        {
      // :pathMatch(.*)* 是 Vue Router 4 的固定写法，匹配所有剩余路径
      path: '/:pathMatch(.*)*', 
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue'),
      meta: { hideTopBar: true }
    },
  ],
})

export default router
