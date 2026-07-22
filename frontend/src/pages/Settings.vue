<template>
  <div class="page">
    <header class="header">
      <button class="back" @click="$router.back()"><span v-html="ICONS.back"></span></button>
      <h1>设置</h1>
    </header>

    <div class="section">
      <div class="item">
        <span>消息通知</span>
        <label class="switch">
          <input type="checkbox" v-model="notifications.message" @change="saveSettings" />
          <span class="slider"></span>
        </label>
      </div>
      <div class="item">
        <span>约球邀请通知</span>
        <label class="switch">
          <input type="checkbox" v-model="notifications.invite" @change="saveSettings" />
          <span class="slider"></span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings } from '../api'
import { ICONS, showToast } from '../utils/ui'

const notifications = ref({ message: true, invite: true })

async function loadSettings() {
  try {
    const res = await getSettings()
    if (res.notifications) notifications.value = res.notifications
  } catch { /* ignore */ }
}

async function saveSettings() {
  try {
    await updateSettings({ notifications: notifications.value })
    showToast('设置已保存')
  } catch (e) {
    showToast(e.message || '保存失败')
  }
}

onMounted(loadSettings)
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
.section { margin: 12px 16px; background: #fff; border-radius: 12px; overflow: hidden; }
.item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; font-size: 15px; border-bottom: 1px solid #f5f5f5;
}
.item:last-child { border-bottom: none; }
.switch { position: relative; width: 46px; height: 26px; display: inline-block; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
  background: #ddd; border-radius: 26px; transition: 0.3s;
}
.slider::before {
  content: ''; position: absolute; height: 20px; width: 20px; left: 3px; bottom: 3px;
  background: #fff; border-radius: 50%; transition: 0.3s;
}
.switch input:checked + .slider { background: #1485ee; }
.switch input:checked + .slider::before { transform: translateX(20px); }
</style>
