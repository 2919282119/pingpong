<template>
  <div class="app">
    <router-view v-if="ready" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()
const ready = ref(false)

onMounted(async () => {
  await userStore.initUserInfo()
  if (!userStore.isLogin && !router.currentRoute.value.path.startsWith('/login') && !router.currentRoute.value.path.startsWith('/register')) {
    router.replace('/login')
  }
  ready.value = true
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --tab-bar-height: 50px;
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  background: #f5f5f5;
  color: #333;
  -webkit-font-smoothing: antialiased;
}
a { text-decoration: none; color: inherit; }
</style>
