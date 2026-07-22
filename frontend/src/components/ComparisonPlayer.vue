<template>
  <div class="player">
    <div class="videos">
      <div class="video-box">
        <div class="video-label">
          <span class="label-badge tmpl">标准模板</span>
          <button class="vid-ctrl" @click="toggleOne('tmpl')" :title="tmplPlaying ? '暂停' : '播放'">
            {{ tmplPlaying ? '⏸' : '▶' }}
          </button>
        </div>
        <div class="video-wrap" @click="toggleOne('tmpl')">
          <video ref="tmplVideo" :src="tmplUrl" muted playsinline preload="auto"
            @timeupdate="onTimeUpdate" @ended="onOneEnded('tmpl')"
          ></video>
          <div v-if="!tmplStarted" class="vid-play-hint">
            <span class="big-play">▶</span>
          </div>
        </div>
      </div>
      <div class="video-box">
        <div class="video-label">
          <span class="label-badge user">你的动作</span>
          <button class="vid-ctrl" @click="toggleOne('user')" :title="userPlaying ? '暂停' : '播放'">
            {{ userPlaying ? '⏸' : '▶' }}
          </button>
        </div>
        <div class="video-wrap" @click="toggleOne('user')">
          <video ref="userVideo" :src="userUrl" muted playsinline preload="auto"
            @timeupdate="onTimeUpdate" @ended="onOneEnded('user')"
          ></video>
          <div v-if="!userStarted" class="vid-play-hint">
            <span class="big-play">▶</span>
          </div>
        </div>
      </div>
    </div>

    <div class="controls">
      <input class="seek-bar" type="range" :min="0" :max="maxDur || 1"
        :value="currentTime" @input="onSeek" step="0.1" />

      <span class="time">{{ fmtTime(currentTime) }} / {{ fmtTime(maxDur) }}</span>

      <div class="speed-group">
        <button v-for="s in speeds" :key="s" class="speed-btn"
          :class="{ active: playbackRate === s }" @click="setSpeed(s)">{{ s }}x</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  userUrl: { type: String, required: true },
  tmplUrl: { type: String, required: true },
})

const tmplVideo = ref(null)
const userVideo = ref(null)
const tmplPlaying = ref(false)
const userPlaying = ref(false)
const tmplStarted = ref(false)
const userStarted = ref(false)
const playbackRate = ref(1)
const currentTime = ref(0)
const maxDur = ref(0)
const speeds = [0.25, 0.5, 1, 2]

function onTimeUpdate() {
  const t = tmplVideo.value?.currentTime || 0
  const u = userVideo.value?.currentTime || 0
  currentTime.value = Math.max(t, u)
  const d = Math.max(tmplVideo.value?.duration || 0, userVideo.value?.duration || 0)
  if (d > 0) maxDur.value = d
}

function toggleOne(side) {
  const v = side === 'tmpl' ? tmplVideo.value : userVideo.value
  if (!v) return
  const playing = side === 'tmpl' ? tmplPlaying : userPlaying
  const started = side === 'tmpl' ? tmplStarted : userStarted
  if (v.ended) { v.currentTime = 0; started.value = false }
  if (playing.value) {
    v.pause()
    playing.value = false
  } else {
    v.play().then(() => { playing.value = true; started.value = true }).catch(() => {})
  }
}

function onOneEnded(side) {
  if (side === 'tmpl') { tmplPlaying.value = false }
  else { userPlaying.value = false }
}

function onSeek(e) {
  const t = parseFloat(e.target.value)
  currentTime.value = t
  if (tmplVideo.value) tmplVideo.value.currentTime = t
  if (userVideo.value) userVideo.value.currentTime = t
}

function setSpeed(s) {
  playbackRate.value = s
  if (tmplVideo.value) tmplVideo.value.playbackRate = s
  if (userVideo.value) userVideo.value.playbackRate = s
}

function fmtTime(s) {
  if (!s || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

onMounted(() => { document.addEventListener('keydown', onKeydown) })

function onKeydown(e) {
  if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
    e.preventDefault()
    toggleOne('tmpl')
  }
}
</script>

<style scoped>
.player { background: #0f0f0f; border-radius: 10px; overflow: hidden; margin-bottom: 16px; }
.videos { display: flex; background: #222; }
.video-box { flex: 1; min-width: 0; background: #000; }
.video-label {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; background: #1a1a1a;
}
.label-badge { font-size: 11px; padding: 2px 10px; border-radius: 4px; font-weight: 600; }
.label-badge.tmpl { background: #e67e22; color: #fff; }
.label-badge.user { background: #3498db; color: #fff; }
.vid-ctrl {
  background: none; border: 1px solid #444; color: #fff; width: 28px; height: 28px;
  border-radius: 4px; cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
}
.vid-ctrl:hover { background: #333; }
.video-wrap {
  position: relative; cursor: pointer;
}
.video-wrap video { width: 100%; height: auto; display: block; max-height: 360px; object-fit: contain; background: #000; }
.vid-play-hint {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.25);
}
.big-play {
  width: 52px; height: 52px; border-radius: 50%; background: rgba(255,255,255,0.9);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #222; padding-left: 4px;
}

.controls {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: #1a1a1a; flex-wrap: wrap;
}
.ctrl-btn {
  background: none; border: 1px solid #444; color: #aaa; height: 30px;
  border-radius: 6px; cursor: pointer; font-size: 11px; padding: 0 10px; white-space: nowrap;
}
.ctrl-btn:hover { border-color: #888; color: #fff; }
.ctrl-btn.active { border-color: #2ecc71; color: #2ecc71; }
.seek-bar { flex: 1; min-width: 60px; height: 4px; accent-color: #3498db; cursor: pointer; }
.time { color: #aaa; font-size: 12px; font-family: monospace; white-space: nowrap; flex-shrink: 0; }
.speed-group { display: flex; gap: 3px; flex-shrink: 0; }
.speed-btn {
  background: none; border: 1px solid #444; color: #aaa;
  padding: 3px 8px; border-radius: 4px; cursor: pointer; font-size: 11px;
}
.speed-btn:hover { border-color: #888; color: #fff; }
.speed-btn.active { background: #3498db; border-color: #3498db; color: #fff; }

@media (max-width: 640px) {
  .videos { flex-direction: column; }
  .video-wrap video { max-height: 240px; }
}
</style>
