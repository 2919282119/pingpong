<template>
  <div class="page">
    <header class="header">
      <h1>动作分析</h1>
    </header>

    <div class="layout">
      <aside class="sidebar" v-if="history.length > 0">
        <div class="sidebar-head">
          <h3>历史记录</h3>
          <button class="clear-btn" @click="clearHistory">清除</button>
        </div>
        <div
          v-for="item in history" :key="item.id"
          class="history-item" :class="{ active: item.id === currentTaskId }"
          @click="loadHistory(item)"
        >
          <span class="hi-type">{{ typeLabel(item.action_type) }}</span>
          <span class="hi-score">{{ item.overall_score }}</span>
          <span class="hi-time">{{ fmtTime(item.created_at) }}</span>
        </div>
      </aside>

      <main class="main">
        <VideoUpload v-if="!report && !loading && !error" @uploaded="onUploaded" />
        <div v-else-if="loading" class="loading-card">
          <div class="preview-wrapper">
            <video
              v-if="templatePreviewUrl" :src="templatePreviewUrl"
              class="preview-video" muted autoplay loop playsinline
            ></video>
            <span v-if="templatePreviewUrl" class="preview-label">标准动作</span>
          </div>
          <div class="loading-bar"><div class="bar-fill"></div></div>
          <p class="loading-text">{{ progressMessage }}</p>
        </div>
        <div v-else-if="error" class="error-card">
          <p>{{ error }}</p>
          <button class="retry-btn" @click="reset">重新上传</button>
        </div>
        <div v-else-if="report" class="report-wrapper">
          <AnalysisReport :report="report" @back="reset" />
        </div>
        <div v-else class="empty-state">
          <p>未能获取分析结果，请重新上传</p>
          <button class="retry-btn" @click="reset">重新上传</button>
        </div>
      </main>
    </div>

    <TabBar :tabs="tabs" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import VideoUpload from '../components/VideoUpload.vue'
import AnalysisReport from '../components/AnalysisReport.vue'
import { uploadVideo, pollAnalysis, getHistory, deleteHistory } from '../api'
import { ICONS } from '../utils/ui'
import TabBar from '../components/TabBar.vue'

const router = useRouter()
const report = ref(null)
const loading = ref(false)
const error = ref('')
const progressMessage = ref('')
const history = ref([])
const currentTaskId = ref(null)
const selectedActionType = ref('')

const POLL_INTERVAL = 1500

const templatePreviewUrl = computed(() => {
  const t = selectedActionType.value
  if (!t) return ''
  return `/media/templates/${t}.mp4`
})

const tabs = computed(() => [
  { label: '首页', icon: ICONS.home, active: false, onClick: () => router.push('/home') },
  { label: '消息', icon: ICONS.message, active: false, onClick: () => router.push('/message') },
  { label: '分析', icon: ICONS.analysis, active: true, onClick: () => {} },
  { label: '我的', icon: ICONS.profile, active: false, onClick: () => router.push('/profile') },
])

onMounted(refreshHistory)

async function onUploaded(file, actionType) {
  selectedActionType.value = actionType
  loading.value = true
  error.value = ''
  progressMessage.value = '正在上传视频...'
  report.value = null

  try {
    const { task_id } = await uploadVideo(file, actionType)
    currentTaskId.value = task_id
    progressMessage.value = '等待处理...'
    await pollUntilDone(task_id)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '上传失败'
    loading.value = false
  }
}

async function pollUntilDone(taskId) {
  while (true) {
    const data = await pollAnalysis(taskId)
    if (data.status === 'done') {
      report.value = data.result
      loading.value = false
      refreshHistory()
      return
    }
    if (data.status === 'error') {
      error.value = data.error || '分析失败'
      loading.value = false
      return
    }
    progressMessage.value = data.progress || '处理中...'
    await new Promise(r => setTimeout(r, POLL_INTERVAL))
  }
}

async function refreshHistory() {
  try { history.value = await getHistory() } catch { /* ignore */ }
}

async function clearHistory() {
  try {
    await deleteHistory()
    history.value = []
    if (!loading.value && !report.value) reset()
  } catch { /* ignore */ }
}

function loadHistory(item) {
  currentTaskId.value = item.id
  loading.value = false
  error.value = ''
  selectedActionType.value = ''
  pollAnalysis(item.id).then(data => {
    if (data.status === 'done' && data.result) report.value = data.result
  })
}

function reset() {
  report.value = null
  error.value = ''
  loading.value = false
  currentTaskId.value = null
  selectedActionType.value = ''
}

function typeLabel(t) {
  const map = { fore_topspin: '正手上旋', back_topspin: '反手上旋', fore_underspin: '正手下旋', back_underspin: '反手下旋' }
  return map[t] || t
}

function fmtTime(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f0f2f5; padding-bottom: calc(var(--tab-bar-height) + var(--safe-area-bottom) + 16px); }
.header {
  background: #fff; text-align: center;
  padding: 14px 16px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03);
}
.header h1 { font-size: 18px; font-weight: 600; color: #1a1a1a; }
/* ── layout ── */
.layout { display: flex; gap: 20px; max-width: 960px; margin: 0 auto; padding: 16px; align-items: flex-start; }
.main { flex: 1; min-width: 0; }
/* ── sidebar ── */
.sidebar { width: 170px; flex-shrink: 0; }
.sidebar-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.sidebar-head h3 { font-size: 13px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; }
.clear-btn { font-size: 11px; padding: 2px 8px; background: none; border: 1px solid #ddd; color: #999; border-radius: 4px; cursor: pointer; }
.clear-btn:hover { color: #e74c3c; border-color: #e74c3c; }
.history-item {
  background: #fff; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;
  cursor: pointer; border: 1px solid transparent; transition: border-color 0.15s, box-shadow 0.15s;
}
.history-item:hover { border-color: #e0e0e0; }
.history-item.active { border-color: #1485ee; box-shadow: 0 0 0 2px rgba(20,133,238,0.1); }
.hi-type { display: block; font-size: 12px; font-weight: 600; color: #444; }
.hi-score { font-size: 20px; font-weight: 700; color: #2ecc71; line-height: 1.2; }
.hi-time { display: block; font-size: 10px; color: #bbb; margin-top: 1px; }
/* ── loading ── */
.loading-card { background: #fff; border-radius: 12px; overflow: hidden; text-align: center; border: 1px solid rgba(0,0,0,0.04); }
.preview-wrapper { position: relative; background: #111; }
.preview-video { width: 100%; max-height: 360px; display: block; object-fit: contain; }
.preview-label {
  position: absolute; top: 12px; left: 12px; color: #fff; font-size: 12px;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(6px); padding: 4px 12px; border-radius: 6px;
}
.loading-bar { height: 4px; background: #e8ecf0; margin: 24px auto 12px; max-width: 320px; border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; width: 60%; background: linear-gradient(90deg, #1485ee, #2ecc71); border-radius: 2px; animation: load 1.8s cubic-bezier(0.4, 0, 0.2, 1) infinite; }
@keyframes load {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}
.loading-text { color: #999; font-size: 14px; padding-bottom: 28px; }
/* ── error / empty ── */
.error-card { background: #fff; border-radius: 12px; padding: 40px; text-align: center; border: 1px solid rgba(0,0,0,0.04); }
.error-card p { color: #e74c3c; margin-bottom: 16px; font-size: 15px; }
.empty-state { background: #fff; border-radius: 12px; padding: 40px; text-align: center; border: 1px solid rgba(0,0,0,0.04); }
.empty-state p { color: #999; margin-bottom: 16px; }
.retry-btn {
  padding: 10px 28px; border: none; border-radius: 8px; background: #1485ee; color: #fff;
  cursor: pointer; font-size: 14px; font-weight: 600; transition: background 0.15s;
}
.retry-btn:hover { background: #0d6efd; }
/* ── mobile ── */
@media (max-width: 768px) {
  .layout { flex-direction: column; padding: 12px; }
  .sidebar { width: 100%; }
  .sidebar-head { display: none; }
  .sidebar { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; scrollbar-width: none; }
  .sidebar::-webkit-scrollbar { display: none; }
  .history-item { min-width: 130px; flex-shrink: 0; margin-bottom: 0; }
}
</style>
