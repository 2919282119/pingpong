<template>
  <div class="upload-card">
    <h3 class="section-title">1. 选择你的击球类型</h3>
    <div class="type-grid">
      <div
        v-for="t in actionTypes" :key="t.value"
        class="type-card" :class="{ active: selectedType === t.value }"
        @click="selectedType = t.value"
      >
        <span class="type-icon">{{ t.icon }}</span>
        <span class="type-label">{{ t.label }}</span>
        <span class="type-desc">{{ t.desc }}</span>
      </div>
    </div>

    <div v-if="selectedType" class="template-preview">
      <div class="preview-video-wrap" :class="{ expanded: previewExpanded }">
        <video
          ref="previewVideo"
          :src="`/media/templates/${selectedType}.mp4`"
          muted loop playsinline preload="auto"
          @click="togglePreview"
          @canplay="tryAutoPlay"
        ></video>
        <div v-if="!previewPlaying" class="play-overlay" @click="togglePreview">
          <span class="play-icon">▶</span>
        </div>
      </div>
      <p class="preview-hint">点击播放示范 · 再次点击放大/缩小</p>
    </div>

    <h3 class="section-title">2. 上传视频</h3>
    <div class="drop-zone" @dragover.prevent @drop.prevent="onDrop" @click="inputRef.click()">
      <p v-if="!file">点击或拖拽视频到此处</p>
      <p v-else class="file-name">{{ file.name }}</p>
      <input
        type="file" accept="video/*" ref="inputRef"
        @change="onSelect" hidden
      />
    </div>

    <div class="actions">
      <button
        class="upload-btn" :disabled="!file || !selectedType"
        @click="upload"
      >
        开始分析
      </button>
    </div>

    <p class="hint">支持 MP4, AVI, MOV, MKV, WebM · 建议视频时长在 15 秒以内</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['uploaded'])

const file = ref(null)
const inputRef = ref(null)
const selectedType = ref('')
const previewExpanded = ref(false)
const previewVideo = ref(null)
const previewPlaying = ref(false)

const actionTypes = [
  { value: 'fore_topspin', icon: '👉', label: '正手拉上旋', desc: '正手对拉' },
  { value: 'back_topspin', icon: '👈', label: '反手拉上旋', desc: '反手对拉' },
  { value: 'fore_underspin', icon: '↗️', label: '正手起下旋', desc: '正手拉下旋球' },
  { value: 'back_underspin', icon: '↖️', label: '反手起下旋', desc: '反手拉下旋球' },
]

function onDrop(e) {
  const f = e.dataTransfer.files[0]
  if (f && f.type.startsWith('video/')) file.value = f
}
function onSelect(e) {
  if (e.target.files[0]) file.value = e.target.files[0]
}
function tryAutoPlay() {
  const v = previewVideo.value
  if (v) {
    v.play().then(() => { previewPlaying.value = true }).catch(() => { previewPlaying.value = false })
  }
}

function togglePreview() {
  const v = previewVideo.value
  if (!v) return
  if (previewPlaying.value) {
    v.pause()
    previewPlaying.value = false
    if (previewExpanded.value) previewExpanded.value = !previewExpanded.value
  } else {
    v.play().then(() => { previewPlaying.value = true }).catch(() => {})
  }
}

function upload() {
  if (file.value && selectedType.value) {
    emit('uploaded', file.value, selectedType.value)
  }
}
</script>

<style scoped>
.upload-card {
  background: #fff; border-radius: 12px; padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;
}
.section-title {
  font-size: 14px; font-weight: 600; color: #555;
  margin-bottom: 12px; text-align: left;
}

.type-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
  margin-bottom: 24px;
}
@media (max-width: 480px) {
  .type-grid { grid-template-columns: 1fr; }
}
.type-card {
  border: 2px solid #e8ecf0; border-radius: 10px; padding: 12px;
  cursor: pointer; transition: all 0.15s; text-align: center;
  display: flex; flex-direction: column; gap: 2px;
}
.type-card:hover { border-color: #b3d9ff; }
.type-card.active { border-color: #3498db; background: #f0f7ff; }
.type-icon { font-size: 20px; }
.type-label { font-weight: 600; font-size: 14px; }
.type-desc { color: #999; font-size: 11px; }

.drop-zone {
  border: 2px dashed #d0d5dd; border-radius: 8px; padding: 36px 16px;
  margin-bottom: 16px; cursor: pointer; transition: border-color 0.2s;
}
.drop-zone:hover { border-color: #3498db; }
.file-name { color: #3498db; font-weight: 500; }

.actions { display: flex; justify-content: center; margin-bottom: 8px; }
.upload-btn {
  padding: 10px 32px; border: none; border-radius: 6px;
  cursor: pointer; font-size: 14px; background: #2ecc71; color: #fff;
}
.upload-btn:hover:not(:disabled) { background: #27ae60; }
.upload-btn:disabled { background: #b3e0c8; cursor: not-allowed; }

.hint { color: #999; font-size: 12px; margin-top: 8px; }

.template-preview {
  margin-bottom: 24px;
  text-align: center;
}
.preview-video-wrap {
  position: relative; display: inline-block; width: 100%;
  border-radius: 8px; overflow: hidden; background: #000;
  cursor: pointer;
}
.preview-video-wrap video {
  width: 100%; max-height: 200px; display: block;
  object-fit: contain; transition: max-height 0.25s; background: #000;
}
.preview-video-wrap.expanded video { max-height: 480px; }
.play-overlay {
  position: absolute; inset: 0; display: flex; align-items: center;
  justify-content: center; background: rgba(0,0,0,0.3);
  transition: background 0.2s;
}
.play-overlay:hover { background: rgba(0,0,0,0.45); }
.play-icon {
  width: 56px; height: 56px; border-radius: 50%; background: rgba(255,255,255,0.9);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; color: #222; padding-left: 4px;
}
.preview-hint {
  color: #999;
  font-size: 11px;
  margin-top: 6px;
}
</style>
