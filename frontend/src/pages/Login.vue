<template>
  <div class="page">
    <div class="icon-area">
      <div class="icon-circle">
        <img src="/pp.ico" class="brand-icon" />
      </div>
    </div>

    <div class="login-card">
      <h1 class="logo">乒小Yo</h1>
      <p class="subtitle">找到你的乒乓球伙伴</p>

      <div class="form">
        <input v-model="email" type="email" placeholder="邮箱" class="input" />
        <input v-model="password" type="password" placeholder="密码" class="input" @keyup.enter="handleLogin" />
        <button class="btn primary" :disabled="loading" @click="handleLogin">{{ loading ? '登录中...' : '登录' }}</button>
      </div>

      <p class="link" @click="$router.push('/register')">没有账号？去注册</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { showToast } from '../utils/ui'

const router = useRouter()
const userStore = useUserStore()
const email = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!email.value || !password.value) {
    showToast('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login({ email: email.value, password: password.value })
    router.replace('/home')
  } catch (e) {
    showToast(e.message || '登录失败')
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
.icon-area { text-align: center; margin-bottom: 32px; }
.icon-circle {
  width: 80px; height: 80px; border-radius: 50%; background: #fff;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.brand-icon { width: 44px; height: 44px; }
.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px 28px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.logo { font-size: 24px; text-align: center; color: #1a1a1a; margin-bottom: 4px; font-weight: 700; }
.subtitle { text-align: center; color: #999; font-size: 13px; margin-bottom: 28px; }
.form { display: flex; flex-direction: column; gap: 14px; }
.input {
  width: 100%; height: 46px; border: 1px solid #e0e0e0; border-radius: 8px;
  padding: 0 14px; font-size: 15px; outline: none; transition: border-color 0.2s;
}
.input:focus { border-color: #1485ee; }
.btn {
  height: 46px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;
  font-weight: 500; transition: opacity 0.2s;
}
.btn.primary { background: #1485ee; color: #fff; }
.btn.primary:disabled { opacity: 0.7; cursor: not-allowed; }
.btn.primary:active:not(:disabled) { opacity: 0.85; }
.link { text-align: center; margin-top: 20px; color: #1485ee; font-size: 14px; cursor: pointer; }
</style>
