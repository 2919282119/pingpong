<template>
  <div class="page">
    <header class="header"><h1>消息</h1></header>

    <!-- Top tabs -->
    <div class="top-tabs">
      <span :class="{ active: tab === 'chat' }" @click="tab = 'chat'">消息</span>
      <span :class="{ active: tab === 'requests' }" @click="tab = 'requests'">
        好友请求
        <span v-if="pendingCount > 0" class="badge-tab">{{ pendingCount }}</span>
      </span>
    </div>

    <!-- Chat conversations -->
    <div class="content" v-if="tab === 'chat'">
      <div v-if="loading" class="status">加载中...</div>
      <div v-else-if="conversations.length === 0" class="status">暂无会话</div>
      <div v-for="c in conversations" :key="c.userId" class="conv-item" @click="$router.push({ path: `/chat/${c.userId}`, query: { name: c.userName, avatar: c.userAvatar } })">
        <img :src="c.userAvatar || DEFAULT_AVATAR" class="avatar" @error="e => e.target.src = DEFAULT_AVATAR" />
        <div class="info">
          <div class="top-row">
            <span class="name">{{ c.userName }}</span>
            <span class="time">{{ fmtTime(c.lastMessageTime) }}</span>
          </div>
          <div class="preview-row">
            <span class="preview">{{ c.lastMessage || '暂无消息' }}</span>
            <span v-if="c.unreadCount > 0" class="badge">{{ c.unreadCount > 99 ? '99+' : c.unreadCount }}</span>
          </div>
        </div>
      </div>
      <div class="clear-bar" v-if="conversations.length > 0">
        <button class="clear-btn" @click="clearAll">清空所有消息</button>
      </div>
    </div>

    <!-- Friend requests -->
    <div class="content" v-else>
      <div v-if="requestsLoading" class="status">加载中...</div>
      <div v-else-if="requests.length === 0" class="status">暂无好友请求</div>
      <div v-for="r in requests" :key="r.id" class="request-item">
        <img :src="r.fromUserAvatar || DEFAULT_AVATAR" class="avatar" @error="e => e.target.src = DEFAULT_AVATAR" @click="$router.push(`/player/${r.fromUserId}`)" />
        <div class="info">
          <span class="name">{{ r.fromUserName }}</span>
        </div>
        <div class="actions">
          <button class="btn accept" @click="handleRequest(r.id, 'accept')">接受</button>
          <button class="btn reject" @click="handleRequest(r.id, 'reject')">拒绝</button>
        </div>
      </div>
    </div>

    <TabBar :tabs="tabs" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getConversations, clearAllMessages, getFriendRequests, handleFriendRequest } from '../api'
import { ICONS, showToast } from '../utils/ui'
import TabBar from '../components/TabBar.vue'

const router = useRouter()
const conversations = ref([])
const loading = ref(true)
const DEFAULT_AVATAR = '/default-avatar.jpg'

// Top tab
const tab = ref('chat')

// Friend requests
const requests = ref([])
const pendingCount = ref(0)
const requestsLoading = ref(false)

const tabs = computed(() => [
  { label: '首页', icon: ICONS.home, active: false, onClick: () => router.push('/home') },
  { label: '消息', icon: ICONS.message, active: true, onClick: () => {} },
  { label: '分析', icon: ICONS.analysis, active: false, onClick: () => router.push('/analysis') },
  { label: '我的', icon: ICONS.profile, active: false, onClick: () => router.push('/profile') },
])

function fmtTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  if (d.toDateString() === now.toDateString()) return `${pad(d.getHours())}:${pad(d.getMinutes())}`
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())}`
}

async function clearAll() {
  try {
    await clearAllMessages()
    conversations.value = []
    showToast('已清空所有消息')
  } catch { showToast('清空失败') }
}

async function loadRequests() {
  requestsLoading.value = true
  try {
    const res = await getFriendRequests()
    requests.value = res.list || []
    pendingCount.value = requests.value.length
  } catch { /* ignore */ }
  finally { requestsLoading.value = false }
}

async function handleRequest(id, action) {
  try {
    await handleFriendRequest(id, action)
    showToast(action === 'accept' ? '已添加球友' : '已拒绝')
    await loadRequests()
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}

onMounted(async () => {
  try {
    const res = await getConversations()
    conversations.value = res.list || []
  } catch { /* ignore */ }
  finally { loading.value = false }
  loadRequests()
})
</script>

<style scoped>
.page { min-height: 100vh; background: #f5f5f5; padding-bottom: calc(var(--tab-bar-height) + var(--safe-area-bottom) + 8px); }
.header {
  background: #fff; text-align: center;
  padding: 14px 16px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03);
}
.header h1 { font-size: 18px; font-weight: 600; color: #1a1a1a; }

/* Top tabs */
.top-tabs {
  display: flex; background: #fff; border-bottom: 1px solid #f0f0f0;
}
.top-tabs span {
  flex: 1; text-align: center; padding: 12px 0; font-size: 14px; color: #666; cursor: pointer;
  position: relative;
}
.top-tabs span.active { color: #1485ee; font-weight: 600; }
.top-tabs span.active::after {
  content: ''; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 24px; height: 3px; background: #1485ee; border-radius: 2px;
}
.badge-tab {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 16px; height: 16px; padding: 0 4px;
  background: #ff4757; color: #fff; font-size: 10px;
  border-radius: 8px; margin-left: 3px; vertical-align: top;
}

.content { padding: 8px 16px; }
.status { text-align: center; color: #999; padding: 40px 0; font-size: 14px; }
.conv-item, .request-item {
  display: flex; gap: 12px; background: #fff; border-radius: 12px; padding: 12px;
  margin-bottom: 10px; cursor: pointer;
}
.conv-item:active, .request-item:active { opacity: 0.8; }
.avatar { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.request-item .avatar { cursor: pointer; }
.info { flex: 1; min-width: 0; }
.top-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.name { font-size: 15px; font-weight: 600; }
.time { font-size: 11px; color: #bbb; }
.preview-row { display: flex; justify-content: space-between; align-items: center; }
.preview { font-size: 13px; color: #999; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: #ff4757; color: #fff; font-size: 11px;
  border-radius: 9px; flex-shrink: 0; margin-left: 6px;
}
.clear-bar { text-align: center; padding: 12px 16px 8px; }
.clear-bar .clear-btn {
  border: none; background: none; color: #ff4757; font-size: 13px; cursor: pointer;
  padding: 8px 20px; border-radius: 6px; transition: background 0.15s;
}
.clear-bar .clear-btn:hover { background: rgba(255,71,87,0.06); }
.actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.btn { padding: 6px 16px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.btn.accept { background: #1485ee; color: #fff; }
.btn.reject { background: #f5f5f5; color: #666; }
</style>
