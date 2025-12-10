// ... imports

const router = createRouter({
  // ... history
  routes: [
    {
      path: '/',
      name: 'main',
      component: () => import('@/views/MainView.vue'),
      // 不需要加 meta，默认显示
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { hideTopBar: true } // 登录页通常也不需要顶栏
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { hideTopBar: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue'),
      meta: { hideTopBar: true } // 404页面也不显示顶栏
    },
  ],
})

export default router