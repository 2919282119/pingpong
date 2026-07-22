<template>
  <div class="page">
    <header class="header">
      <button class="back" @click="$router.back()"><span v-html="ICONS.back"></span></button>
      <h1>编辑资料</h1>
      <button class="save" @click="save">保存</button>
    </header>

    <div class="form">
      <!-- 背景图 -->
      <div class="bg-section" :style="{ backgroundImage: bgImageUrl }" @click="pickBg">
        <input ref="bgInput" type="file" accept="image/*" hidden @change="onBgChange" />
        <div class="bg-overlay">
          <span class="camera-icon" v-html="ICONS.camera"></span>
          <span>更换封面</span>
        </div>
      </div>

      <!-- 头像 -->
      <div class="avatar-section">
        <div class="avatar-wrapper" @click="pickAvatar">
          <input ref="avatarInput" type="file" accept="image/*" hidden @change="onAvatarChange" />
          <img :src="avatarPreview" class="avatar-img" />
          <div class="avatar-overlay">
            <span class="camera-icon" v-html="ICONS.camera"></span>
          </div>
        </div>
        <span class="avatar-hint">点击更换头像</span>
      </div>

      <div class="field">
        <label>昵称</label>
        <input v-model="form.name" type="text" placeholder="请输入昵称" />
      </div>
      <div class="field">
        <label>性别</label>
        <div class="radio-group">
          <label class="radio" :class="{ active: form.gender === '男' }">
            <input type="radio" value="男" v-model="form.gender" /> 男
          </label>
          <label class="radio" :class="{ active: form.gender === '女' }">
            <input type="radio" value="女" v-model="form.gender" /> 女
          </label>
        </div>
      </div>
      <div class="field">
        <label>出生日期</label>
        <input v-model="form.birthdate" type="date" />
      </div>
      <div class="field">
        <label>开始打球年份</label>
        <input v-model="form.startPlayingYear" type="number" placeholder="如 2018" />
      </div>
      <div class="field">
        <label>打法</label>
        <select v-model="form.playStyle">
          <option value="">请选择</option>
          <option v-for="s in playStyles" :key="s">{{ s }}</option>
        </select>
      </div>
      <div class="field">
        <label>自我介绍</label>
        <textarea v-model="form.selfDescription" placeholder="介绍一下自己..." rows="3"></textarea>
      </div>
      <div class="field">
        <label>地址</label>
        <input v-model="form.address" type="text" placeholder="如 北京市朝阳区" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { updateUserInfo, uploadImage } from '../api'
import { ICONS, showToast } from '../utils/ui'

const router = useRouter()
const userStore = useUserStore()
const playStyles = ['快攻弧圈', '削球', '全面型', '防守反攻', '近台快攻', '其他']
const DEFAULT_AVATAR = '/default-avatar.jpg'
const DEFAULT_BG = '/default-bg.jpg'

const form = ref({ ...userStore.userInfo })
const avatarPreview = ref(userStore.userInfo.avatar || DEFAULT_AVATAR)
const avatarInput = ref(null)
const bgInput = ref(null)
const uploading = ref(false)

const bgImageUrl = computed(() => {
  const bg = form.value.bgImg
  const url = bg ? bg : DEFAULT_BG
  return `url(${url})`
})

function pickAvatar() {
  avatarInput.value?.click()
}

function pickBg() {
  bgInput.value?.click()
}

async function onAvatarChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  try {
    const res = await uploadImage(file)
    form.value.avatar = res.url
    avatarPreview.value = res.url
  } catch (err) {
    showToast('头像上传失败')
  }
}

async function onBgChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  try {
    const res = await uploadImage(file)
    form.value.bgImg = res.url
  } catch (err) {
    showToast('背景上传失败')
  }
}

async function save() {
  if (uploading.value) return
  uploading.value = true
  try {
    await updateUserInfo({
      name: form.value.name,
      gender: form.value.gender,
      birthdate: form.value.birthdate,
      startPlayingYear: form.value.startPlayingYear,
      playStyle: form.value.playStyle,
      selfDescription: form.value.selfDescription,
      address: form.value.address,
      avatar: form.value.avatar,
      bgImg: form.value.bgImg,
    })
    userStore.setUserInfo({ ...form.value })
    showToast('保存成功')
    router.back()
  } catch (e) {
    showToast(e.message || '保存失败')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f5f5f5; }
.header {
  display: flex; align-items: center; padding: 10px 16px;
  background: rgba(255,255,255,0.72); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0,0,0,0.06); position: sticky; top: 0; z-index: 10;
}
.back { width: 32px; height: 32px; border: none; background: none; cursor: pointer; color: #333; }
.back :deep(svg) { width: 24px; height: 24px; fill: #333; }
.header h1 { flex: 1; font-size: 17px; font-weight: 600; text-align: center; }
.save { border: none; background: none; color: #1485ee; font-size: 15px; cursor: pointer; font-weight: 600; }
.form { margin: 0; }
/* bg section */
.bg-section {
  height: 160px; background-size: cover; background-position: center;
  background-color: #1485ee; position: relative; cursor: pointer;
}
.bg-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,0.3);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #fff; font-size: 13px; gap: 6px; opacity: 0; transition: opacity 0.2s;
}
.bg-section:hover .bg-overlay { opacity: 1; }
/* avatar section */
.avatar-section {
  display: flex; flex-direction: column; align-items: center; padding: 16px;
  margin-top: -40px; position: relative; z-index: 1;
}
.avatar-wrapper {
  width: 80px; height: 80px; border-radius: 50%; overflow: hidden;
  border: 3px solid #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  cursor: pointer; position: relative;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.2s;
}
.avatar-wrapper:hover .avatar-overlay { opacity: 1; }
.avatar-hint { font-size: 12px; color: #999; margin-top: 8px; }
.camera-icon { width: 24px; height: 24px; display: flex; }
.camera-icon :deep(svg) { width: 24px; height: 24px; fill: #fff; }
/* fields */
.form > .field { padding: 14px 16px; background: #fff; border-bottom: 1px solid #f5f5f5; }
.field label { display: block; font-size: 13px; color: #666; margin-bottom: 6px; }
.field input, .field select, .field textarea {
  width: 100%; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px 12px;
  font-size: 14px; outline: none; background: #fff;
}
.field input:focus, .field select:focus, .field textarea:focus { border-color: #1485ee; }
.radio-group { display: flex; gap: 12px; }
.radio {
  padding: 8px 24px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; cursor: pointer;
}
.radio input { display: none; }
.radio.active { border-color: #1485ee; color: #1485ee; background: rgba(20,133,238,0.05); }
</style>
