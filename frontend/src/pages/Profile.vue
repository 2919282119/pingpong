<template>
  <div class="page">
    <div class="profile-header" :style="{ backgroundImage: bgUrl }">
      <div class="header-overlay"></div>
      <img :src="userStore.getUserAvatar" class="avatar" @error="e => e.target.src = DEFAULT_AVATAR" />
      <h2 class="name">{{ userStore.userInfo.name || '未设置昵称' }}</h2>
      <p class="desc">{{ userStore.userInfo.selfDescription || '这个人很懒，什么都没写' }}</p>
    </div>

    <div class="menu-list">
      <div class="menu-item" @click="$router.push('/profile/edit')">
        <span class="menu-icon" v-html="ICONS.person"></span>
        <span class="label">编辑资料</span>
        <span class="arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/friends')">
        <span class="menu-icon" v-html="ICONS.friends"></span>
        <span class="label">我的球友</span>
        <span class="arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/settings')">
        <span class="menu-icon" v-html="ICONS.settings"></span>
        <span class="label">设置</span>
        <span class="arrow">&#8250;</span>
      </div>
    </div>

    <button class="logout-btn" @click="handleLogout">退出登录</button>

    <TabBar :tabs="tabs" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ICONS, showToast } from '../utils/ui'
import TabBar from '../components/TabBar.vue'

const router = useRouter()
const userStore = useUserStore()
const DEFAULT_AVATAR = '/default-avatar.jpg'
const DEFAULT_BG = '/default-bg.jpg'

const bgUrl = computed(() => {
  const bg = userStore.userInfo.bgImg
  return bg ? `url(${bg})` : `url(${DEFAULT_BG})`
})

const tabs = computed(() => [
  { label: '首页', icon: ICONS.home, active: false, onClick: () => router.push('/home') },
  { label: '消息', icon: ICONS.message, active: false, onClick: () => router.push('/message') },
  { label: '分析', icon: ICONS.analysis, active: false, onClick: () => router.push('/analysis') },
  { label: '我的', icon: ICONS.profile, active: true, onClick: () => {} },
])

async function handleLogout() {
  await userStore.logout()
  showToast('已退出')
  router.replace('/login')
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f5f5f5; padding-bottom: calc(var(--tab-bar-height) + var(--safe-area-bottom) + 8px); }
.profile-header {
  position: relative; padding: 40px 20px 28px; text-align: center;
  background-size: cover; background-position: center;
  background-color: #1485ee;
  color: #fff; overflow: hidden;
}
.header-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.15), rgba(0,0,0,0.5));
  z-index: 0;
}
.profile-header > * { position: relative; z-index: 1; }
.avatar {
  width: 80px; height: 80px; border-radius: 50%; object-fit: cover;
  border: 3px solid rgba(255,255,255,0.5); margin-bottom: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
.name { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
.desc { font-size: 13px; opacity: 0.85; }
.menu-list { margin: 12px 16px; background: #fff; border-radius: 12px; overflow: hidden; }
.menu-item {
  display: flex; align-items: center; padding: 14px 16px; cursor: pointer;
  border-bottom: 1px solid #f5f5f5; font-size: 15px; color: #333;
}
.menu-item:last-child { border-bottom: none; }
.menu-icon { width: 20px; height: 20px; margin-right: 12px; display: flex; color: #666; }
.menu-icon :deep(svg) { width: 20px; height: 20px; fill: #666; }
.menu-item .label { flex: 1; }
.arrow { font-size: 18px; color: #ccc; }
.logout-btn {
  display: block; width: calc(100% - 32px); margin: 20px auto 0; height: 44px;
  background: #fff; color: #ff4757; border: none; border-radius: 10px;
  font-size: 15px; cursor: pointer;
}
.logout-btn:active { background: #f5f5f5; }
</style>
