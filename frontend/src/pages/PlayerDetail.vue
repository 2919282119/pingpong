<template>
  <div class="page">
    <header class="header">
      <button class="back" @click="$router.back()">
        <span v-html="ICONS.back"></span>
      </button>
      <h1>球友详情</h1>
    </header>

    <div v-if="loading" class="status">加载中...</div>
    <div v-else-if="player" class="content">
      <!-- 背景封面 -->
      <div class="cover" :style="{ backgroundImage: `url(${player.bgImg || DEFAULT_BG})` }">
        <div class="cover-overlay"></div>
      </div>

      <!-- 头像 + 信息 -->
      <div class="profile-card">
        <img :src="player.avatar || DEFAULT_AVATAR" class="avatar" />
        <h2>{{ player.name }}</h2>
        <div class="tags">
          <span>{{ player.gender }}</span>
          <span v-if="player.age">{{ player.age }}岁</span>
          <span v-if="player.experience">球龄{{ player.experience }}年</span>
        </div>
        <p class="intro">{{ player.introduction || '这个人很懒，什么都没写' }}</p>
        <div class="distance-badge" v-if="player.distance">相距 {{ player.distance }}km</div>

        <div class="actions">
          <button class="btn chat" @click="$router.push({ path: `/chat/${player.id}`, query: { name: player.name, avatar: player.avatar } })">
            <span v-html="ICONS.chat"></span> 发消息
          </button>
          <button v-if="!player.isFriend && !requestSent" class="btn add" @click="addFriend">加球友</button>
          <button v-else-if="requestSent" class="btn pending" disabled>已发送请求</button>
          <button v-else class="btn added" disabled>已是球友</button>
        </div>
      </div>

      <div class="info-section">
        <div class="info-row"><span class="label">打法</span><span>{{ player.playStyle || '未设置' }}</span></div>
        <div class="info-row"><span class="label">地区</span><span>{{ player.address || '未设置' }}</span></div>
      </div>
    </div>
    <div v-else class="status">球友不存在</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getPlayerDetail, sendFriendRequest, checkFriendship } from '../api'
import { ICONS, showToast } from '../utils/ui'

const route = useRoute()
const player = ref(null)
const loading = ref(true)
const requestSent = ref(false)
const DEFAULT_AVATAR = '/default-avatar.jpg'
const DEFAULT_BG = '/default-bg.jpg'

onMounted(async () => {
  try {
    const res = await getPlayerDetail(route.params.id)
    player.value = res
    if (!res.isFriend) {
      const check = await checkFriendship(route.params.id)
      requestSent.value = check.hasPendingRequest
    }
  } catch { /* ignore */ }
  finally { loading.value = false }
})

async function addFriend() {
  try {
    await sendFriendRequest({ toUserId: route.params.id })
    requestSent.value = true
    showToast('好友请求已发送')
  } catch (e) {
    showToast(e.message || '发送失败')
  }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f5f5f5; }
.header {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: rgba(255,255,255,0.72); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0,0,0,0.06); position: sticky; top: 0; z-index: 10;
}
.back { width: 32px; height: 32px; border: none; background: none; cursor: pointer; color: #333; }
.back :deep(svg) { width: 24px; height: 24px; fill: #333; }
.header h1 { font-size: 17px; font-weight: 600; }
.status { text-align: center; color: #999; padding: 60px 0; font-size: 14px; }
/* ── cover ── */
.cover {
  height: 200px; background-size: cover; background-position: center;
  background-color: #1485ee; position: relative; border-radius: 12px 12px 0 0;
}
.cover-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.4));
  border-radius: 12px 12px 0 0;
}
/* ── profile card ── */
.content { padding: 16px; }
.profile-card {
  background: #fff; border-radius: 0 0 12px 12px; padding: 0 24px 24px;
  text-align: center; margin-top: -40px; position: relative; z-index: 1;
}
.avatar {
  width: 80px; height: 80px; border-radius: 50%; object-fit: cover;
  margin-top: -40px; border: 3px solid #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 12px;
}
.profile-card h2 { font-size: 20px; margin-bottom: 8px; }
.tags { display: flex; gap: 8px; justify-content: center; margin-bottom: 12px; }
.tags span { font-size: 12px; background: #f0f2f5; padding: 2px 10px; border-radius: 10px; color: #666; }
.intro { font-size: 14px; color: #999; margin-bottom: 12px; }
.distance-badge { display: inline-block; font-size: 13px; color: #1485ee; background: rgba(20,133,238,0.08); padding: 4px 14px; border-radius: 12px; margin-bottom: 16px; }
.actions { display: flex; gap: 12px; }
.btn { flex: 1; height: 44px; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; }
.btn :deep(svg) { width: 18px; height: 18px; fill: currentColor; }
.btn.chat { background: #1485ee; color: #fff; }
.btn.add { background: #fff; color: #1485ee; border: 1px solid #1485ee; }
.btn.added { background: #f5f5f5; color: #ccc; border: 1px solid #e0e0e0; cursor: not-allowed; }
.btn.pending { background: #f5f5f5; color: #999; border: 1px solid #ddd; cursor: not-allowed; }
.btn:active:not(:disabled) { opacity: 0.85; }
.info-section { background: #fff; border-radius: 12px; margin-top: 12px; }
.info-row { display: flex; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid #f5f5f5; font-size: 14px; }
.info-row:last-child { border-bottom: none; }
.label { color: #999; }
</style>
