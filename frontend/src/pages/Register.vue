<template>
  <div class="page">
    <div class="icon-area">
      <div class="icon-circle">
        <img src="/pp.ico" class="brand-icon" />
      </div>
    </div>
    <div class="register-card">
      <h1 class="logo">注册账号</h1>
      <p class="subtitle">加入乒小Yo，找到你的球友</p>

      <div class="form">
        <input v-model="email" type="email" placeholder="邮箱" class="input" />
        <div class="code-row">
          <input v-model="verifyCode" type="text" placeholder="验证码" class="input" />
          <button class="btn code-btn" :disabled="codeSending || codeCountdown > 0" @click="sendCode">
            {{ codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
          </button>
        </div>
        <input v-model="nickname" type="text" placeholder="昵称" class="input" />
        <input v-model="password" type="password" placeholder="密码（至少6位）" class="input" />
        <div class="gender-row">
          <label class="gender-option" :class="{ active: gender === '男' }">
            <input type="radio" value="男" v-model="gender" /> 男
          </label>
          <label class="gender-option" :class="{ active: gender === '女' }">
            <input type="radio" value="女" v-model="gender" /> 女
          </label>
        </div>
        <button class="btn primary" :disabled="loading" @click="handleRegister">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </div>

      <p class="link" @click="$router.push('/login')">已有账号？去登录</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { sendVerifyCode } from '../api'
import { showToast } from '../utils/ui'

const router = useRouter()
const userStore = useUserStore()
const email = ref('')
const verifyCode = ref('')
const nickname = ref('')
const password = ref('')
const gender = ref('男')
const loading = ref(false)
const codeSending = ref(false)
const codeCountdown = ref(0)

async function sendCode() {
  if (!email.value) { showToast('请输入邮箱'); return }
  codeSending.value = true
  try {
    const res = await sendVerifyCode({ email: email.value, type: 'register' })
    showToast(res.message || '验证码已发送')
    codeCountdown.value = 60
    const timer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    showToast(e.message || '发送失败')
  } finally {
    codeSending.value = false
  }
}

async function handleRegister() {
  if (!email.value || !verifyCode.value || !nickname.value || !password.value) {
    showToast('请填写完整信息')
    return
  }
  if (password.value.length < 6) { showToast('密码长度不能少于6位'); return }
  loading.value = true
  try {
    await userStore.register({ email: email.value, verifyCode: verifyCode.value, nickname: nickname.value, password: password.value, gender: gender.value })
    router.replace('/home')
  } catch (e) {
    showToast(e.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1485ee 0%, #0d6efd 100%);
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 20px 20px;
}
.register-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.logo { font-size: 24px; text-align: center; color: #1a1a1a; margin-bottom: 4px; font-weight: 700; }
.icon-area { text-align: center; margin-bottom: 32px; width: 100%; max-width: 380px; }
.icon-circle {
  width: 80px; height: 80px; border-radius: 50%; background: #fff;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.brand-icon { width: 44px; height: 44px; }
.subtitle { text-align: center; color: #999; font-size: 13px; margin-bottom: 24px; }
.form { display: flex; flex-direction: column; gap: 12px; }
.input {
  width: 100%; height: 44px; border: 1px solid #e0e0e0; border-radius: 8px;
  padding: 0 14px; font-size: 14px; outline: none;
}
.input:focus { border-color: #1485ee; }
.code-row { display: flex; gap: 10px; }
.code-row .input { flex: 1; }
.code-btn {
  height: 44px; padding: 0 16px; white-space: nowrap; border: 1px solid #1485ee;
  background: #fff; color: #1485ee; border-radius: 8px; font-size: 13px; cursor: pointer;
}
.code-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.gender-row { display: flex; gap: 12px; }
.gender-option {
  flex: 1; height: 44px; display: flex; align-items: center; justify-content: center;
  border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; cursor: pointer;
}
.gender-option input { display: none; }
.gender-option.active { border-color: #1485ee; color: #1485ee; background: rgba(20,133,238,0.05); }
.btn {
  height: 44px; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; font-weight: 500;
}
.btn.primary { background: #1485ee; color: #fff; }
.btn.primary:disabled { opacity: 0.7; cursor: not-allowed; }
.link { text-align: center; margin-top: 20px; color: #1485ee; font-size: 14px; cursor: pointer; }
</style>
