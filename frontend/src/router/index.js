import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../pages/Home.vue'),
    meta: { tab: true, tabIndex: 0, title: '首页' },
  },
  {
    path: '/message',
    name: 'Message',
    component: () => import('../pages/Message.vue'),
    meta: { tab: true, tabIndex: 1, title: '消息' },
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('../pages/Analysis.vue'),
    meta: { tab: true, tabIndex: 2, title: '动作分析' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../pages/Profile.vue'),
    meta: { tab: true, tabIndex: 3, title: '我的' },
  },
  { path: '/login', name: 'Login', component: () => import('../pages/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../pages/Register.vue') },
  { path: '/player/:id', name: 'PlayerDetail', component: () => import('../pages/PlayerDetail.vue') },
  { path: '/chat/:id', name: 'Chat', component: () => import('../pages/Chat.vue') },
  { path: '/profile/edit', name: 'EditProfile', component: () => import('../pages/EditProfile.vue') },
  { path: '/friends', name: 'Friends', component: () => import('../pages/Friends.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../pages/Settings.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
