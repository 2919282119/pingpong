<template>
  <div class="page">
    <header class="header">
      <button class="back" @click="$router.back()"><span v-html="ICONS.back"></span></button>
      <h1>我的球友</h1>
    </header>

    <div class="tabs">
      <span :class="{ active: tab === 'list' }" @click="tab = 'list'">球友列表</span>
      <span :class="{ active: tab === 'requests' }" @click="tab = 'requests'">
        好友请求
        <span v-if="pendingCount > 0" class="badge">{{ pendingCount }}</span>
      </span>
    </div>

    <div class="content">
      <!-- Friends list -->
      <div v-if="tab === 'list'">
        <div v-if="friends.length === 0" class="status">暂无球友</div>
        <div v-for="f in friends" :key="f.id" class="friend-item" @click="$router.push(`/player/${f.id}`)">
          <img :src="f.avatar || DEFAULT_AVATAR" class="avatar" />
          <div class="info">
            <span class="name">{{ f.nickname }}</span>
            <span v-if="f.online" class="online">在线</span>
            <span v-else class="offline">离线</span>
          </div>
        </div>
      </div>

      <!-- Requests -->
      <div v-else>
        <div v-if="requests.length === 0" class="status">暂无好友请求</div>
        <div v-for="r in requests" :key="r.id" class="request-item">
          <img :src="r.fromUserAvatar || DEFAULT_AVATAR" class="avatar" />
          <div class="info">
            <span class="name">{{ r.fromUserName }}</span>
          </div>
          <div class="actions">
            <button class="btn accept" @click="handleRequest(r.id, 'accept')">接受</button>
            <button class="btn reject" @click="handleRequest(r.id, 'reject')">拒绝</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFriendsList, getFriendRequests, handleFriendRequest } from '../api'
import { ICONS, showToast } from '../utils/ui'

const DEFAULT_AVATAR = '/default-avatar.jpg'
const tab = ref('list')
const friends = ref([])
const requests = ref([])
const pendingCount = ref(0)

async function loadFriends() {
  try {
    const res = await getFriendsList()
    friends.value = res.list || []
  } catch { /* ignore */ }
}

async function loadRequests() {
  try {
    const res = await getFriendRequests()
    requests.value = res.list || []
    pendingCount.value = requests.value.length
  } catch { /* ignore */ }
}

async function handleRequest(id, action) {
  try {
    await handleFriendRequest(id, action)
    showToast(action === 'accept' ? '已添加球友' : '已拒绝')
    await loadRequests()
    await loadFriends()
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}

onMounted(() => { loadFriends(); loadRequests() })
</script>

<style scoped>
.page { min-height: 100vh; background: #f5f5f5; }
.header {
  display: flex; align-items: center; padding: 10px 16px;
  background: rgba(255,255,255,0.72); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.back { width: 32px; height: 32px; border: none; background: none; cursor: pointer; color: #333; }
.back :deep(svg) { width: 24px; height: 24px; fill: #333; }
.header h1 { flex: 1; font-size: 17px; font-weight: 600; text-align: center; }
.tabs {
  display: flex; background: #fff; border-bottom: 1px solid #f0f0f0;
}
.tabs span {
  flex: 1; text-align: center; padding: 14px 0; font-size: 14px; color: #666; cursor: pointer;
  position: relative;
}
.tabs span.active { color: #1485ee; font-weight: 600; }
.tabs span.active::after {
  content: ''; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 24px; height: 3px; background: #1485ee; border-radius: 2px;
}
.badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: #ff4757; color: #fff; font-size: 11px;
  border-radius: 9px; margin-left: 4px;
}
.content { padding: 8px 16px; }
.status { text-align: center; color: #999; padding: 40px 0; font-size: 14px; }
.friend-item, .request-item {
  display: flex; align-items: center; gap: 12px; background: #fff;
  border-radius: 10px; padding: 12px; margin-bottom: 8px; cursor: pointer;
}
.avatar { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.info { flex: 1; display: flex; align-items: center; gap: 8px; }
.name { font-size: 15px; font-weight: 500; }
.online { font-size: 11px; color: #2ecc71; }
.offline { font-size: 11px; color: #bbb; }
.actions { display: flex; gap: 8px; }
.btn { padding: 6px 16px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.btn.accept { background: #1485ee; color: #fff; }
.btn.reject { background: #f5f5f5; color: #666; }
</style>
