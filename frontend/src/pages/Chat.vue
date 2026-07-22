<template>
  <div class="page">
    <header class="header">
      <button class="back" @click="$router.back()">
        <span v-html="ICONS.back"></span>
      </button>
      <img :src="userAvatar" class="avatar-mini" @error="e => e.target.src = DEFAULT_AVATAR" @click="goToPlayer" />
      <h1>{{ userName }}</h1>
    </header>

    <div class="messages" ref="msgContainer">
      <div v-if="messages.length === 0" class="empty">开始聊天吧</div>
      <div v-for="msg in messages" :key="msg.id" class="msg-row" :class="{ mine: msg.fromUserId === myId }">
        <div class="bubble">{{ msg.content }}</div>
        <span class="time">{{ fmtTime(msg.createTime) }}</span>
      </div>
    </div>

    <div class="input-bar">
      <input v-model="inputText" type="text" placeholder="输入消息..." @keyup.enter="sendMsg" />
      <button @click="sendMsg" :disabled="!inputText.trim()">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getChatMessages } from '../api'
import { useUserStore } from '../stores/user'
import { ICONS, showToast } from '../utils/ui'
import wsManager from '../utils/websocket'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const DEFAULT_AVATAR = '/default-avatar.jpg'
const myId = userStore.userInfo.id
const userName = route.query.name || '球友'
const userAvatar = route.query.avatar || DEFAULT_AVATAR
const messages = ref([])
const inputText = ref('')
const msgContainer = ref(null)

function scrollBottom() {
  nextTick(() => {
    if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  })
}

function fmtTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function goToPlayer() {
  router.push(`/player/${route.params.id}`)
}

async function loadMessages() {
  try {
    const res = await getChatMessages({ userId: route.params.id })
    messages.value = res.list || []
    scrollBottom()
  } catch { /* ignore */ }
}

async function sendMsg() {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''

  wsManager.send({
    type: 'chat',
    toUserId: route.params.id,
    content: text,
  })
}

function handleChatMsg(data) {
  const msg = data.message
  if (String(msg.fromUserId) === String(route.params.id) || String(msg.toUserId) === String(route.params.id)) {
    const exists = messages.value.some(m => m.id === msg.id)
    if (!exists) {
      messages.value.push(msg)
      scrollBottom()
    }
  }
}

onMounted(async () => {
  await loadMessages()
  wsManager.on('chat', handleChatMsg)

  if (!wsManager.isConnected) {
    wsManager.connect(myId).catch(() => {})
  }
})
</script>

<style scoped>
.page {
  height: 100vh; display: flex; flex-direction: column; background: #ededed;
}
/* --- fixed top header --- */
.header {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: rgba(255,255,255,0.72); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  flex-shrink: 0; border-bottom: 1px solid rgba(0,0,0,0.06);
}
.back { width: 32px; height: 32px; border: none; background: none; cursor: pointer; color: #333; padding: 0; display: flex; align-items: center; }
.back :deep(svg) { width: 22px; height: 22px; fill: #333; }
.avatar-mini {
  width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex-shrink: 0;
  cursor: pointer;
}
.header h1 { font-size: 16px; font-weight: 600; color: #111; }
/* --- scrollable messages --- */
.messages {
  flex: 1; overflow-y: auto; padding: 12px 16px;
  display: flex; flex-direction: column;
}
.empty { text-align: center; color: #b0b0b0; padding: 60px 0; font-size: 14px; }
.msg-row {
  margin-bottom: 14px; max-width: min(75%, 300px); width: fit-content;
}
.msg-row:not(.mine) { margin-right: auto; }
.msg-row.mine { margin-left: auto; }
.bubble {
  padding: 10px 14px; border-radius: 16px; font-size: 15px; line-height: 1.45;
  background: #fff; color: #222;
  overflow-wrap: break-word; word-break: break-word;
}
.msg-row.mine .bubble {
  background: #1485ee; color: #fff;
}
.time { font-size: 11px; color: #b4b4b4; margin-top: 3px; display: block; }
.msg-row.mine .time { text-align: right; }
/* --- fixed bottom bar --- */
.input-bar {
  display: flex; gap: 10px; padding: 10px 16px;
  background: #fff; flex-shrink: 0;
  border-top: 1px solid rgba(0,0,0,0.06);
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
}
.input-bar input {
  flex: 1; height: 40px; border: none; background: #f5f5f5;
  border-radius: 20px; padding: 0 18px; font-size: 15px; outline: none;
  transition: background 0.2s;
}
.input-bar input:focus { background: #eee; }
.input-bar button {
  height: 40px; padding: 0 22px; border: none; border-radius: 20px;
  background: #1485ee; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s; white-space: nowrap;
}
.input-bar button:active:not(:disabled) { opacity: 0.8; }
.input-bar button:disabled { background: #ccc; cursor: not-allowed; }
</style>
