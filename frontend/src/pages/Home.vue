<template>
  <div class="page">
    <header class="header">
      <span class="brand">
        <img src="/pp.ico" class="brand-icon" />
        <h1>乒小Yo</h1>
      </span>
    </header>

    <!-- Search + Filter -->
    <div class="toolbar">
      <div class="search-box">
        <span class="search-icon" v-html="ICONS.search"></span>
        <input v-model="keyword" type="text" placeholder="搜索用户名" @keyup.enter="searchPlayers" />
      </div>
      <button class="filter-btn" @click="showFilter = !showFilter">筛选</button>
    </div>

    <!-- Filter panel -->
    <div class="filter-panel" v-if="showFilter">
      <div class="filter-row">
        <span class="filter-label">性别</span>
        <div class="filter-opts">
          <span v-for="g in ['全部','男','女']" :key="g"
            :class="{ active: filterGender === (g === '全部' ? '' : g) }"
            @click="filterGender = (g === '全部' ? '' : g)">{{ g }}</span>
        </div>
      </div>
      <div class="filter-row">
        <span class="filter-label">打法</span>
        <div class="filter-opts">
          <span v-for="s in ['全部', ...playStyles]" :key="s"
            :class="{ active: filterPlayStyle === (s === '全部' ? '' : s) }"
            @click="filterPlayStyle = (s === '全部' ? '' : s)">{{ s }}</span>
        </div>
      </div>
      <div class="filter-row">
        <span class="filter-label">年龄</span>
        <div class="filter-opts age-range">
          <input v-model.number="filterAgeMin" type="number" placeholder="最小" min="3" max="100" />
          <span class="sep">—</span>
          <input v-model.number="filterAgeMax" type="number" placeholder="最大" min="3" max="100" />
        </div>
      </div>
      <div class="filter-row">
        <span class="filter-label">距离</span>
        <div class="filter-opts">
          <span v-for="d in distanceOptions" :key="d.label"
            :class="{ active: filterDistance === d.val }"
            @click="filterDistance = d.val">{{ d.label }}</span>
        </div>
      </div>
      <div class="filter-actions">
        <button class="reset-btn" @click="resetFilter">重置</button>
        <button class="apply-btn" @click="applyFilter">应用筛选</button>
      </div>
    </div>

    <!-- Player list -->
    <div class="content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="players.length === 0" class="empty">暂无附近球友</div>
      <div v-for="p in players" :key="p.id" class="player-card" @click="$router.push(`/player/${p.id}`)">
        <img :src="p.avatar || DEFAULT_AVATAR" class="avatar" @error="e => e.target.src = DEFAULT_AVATAR" />
        <div class="info">
          <div class="name-row">
            <span class="name">{{ p.name }}</span>
            <span class="gender" :class="p.gender === '女' ? 'female' : 'male'">{{ p.gender }}</span>
            <span class="age">{{ p.age ?? '?' }}岁</span>
          </div>
          <div class="tags">
            <span v-if="p.experience">球龄{{ p.experience }}年</span>
            <span v-if="p.playStyle">{{ p.playStyle }}</span>
          </div>
          <span class="distance">{{ p.distance }}km</span>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="pagination">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <template v-for="n in totalPages" :key="n">
          <span v-if="Math.abs(n - page) <= 2 || n === 1 || n === totalPages"
                :class="{ active: n === page }" @click="goPage(n)">{{ n }}</span>
          <span v-else-if="n === 2 && page > 4">…</span>
          <span v-else-if="n === totalPages - 1 && page < totalPages - 3">…</span>
        </template>
        <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      </div>
      <div v-if="!loading && total > 0" class="page-info">共 {{ total }} 位球友</div>
    </div>

    <TabBar :tabs="tabs" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getNearbyPlayers, updateLocation } from '../api'
import { useUserStore } from '../stores/user'
import { ICONS, showToast } from '../utils/ui'
import TabBar from '../components/TabBar.vue'

const router = useRouter()
const userStore = useUserStore()

const DEFAULT_AVATAR = '/default-avatar.jpg'
const playStyles = ['快攻弧圈', '削球', '全面型', '防守反攻', '近台快攻', '其他']
const distanceOptions = [
  { label: '全部', val: '' },
  { label: '< 5km', val: '0-5' },
  { label: '5-10km', val: '5-10' },
  { label: '> 10km', val: '10+' },
]

const players = ref([])
const loading = ref(false)
const keyword = ref('')
const showFilter = ref(false)
const filterGender = ref('')
const filterPlayStyle = ref('')
const filterDistance = ref('')
const filterAgeMin = ref(null)
const filterAgeMax = ref(null)
const page = ref(1)
const total = ref(0)
const pageSize = 10
const userCoords = ref({
  latitude: userStore.userInfo.latitude || 30,
  longitude: userStore.userInfo.longitude || 120,
})

const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

const tabs = computed(() => [
  { label: '首页', icon: ICONS.home, active: true, onClick: () => {} },
  { label: '消息', icon: ICONS.message, active: false, onClick: () => router.push('/message') },
  { label: '分析', icon: ICONS.analysis, active: false, onClick: () => router.push('/analysis') },
  { label: '我的', icon: ICONS.profile, active: false, onClick: () => router.push('/profile') },
])

async function loadPlayers() {
  loading.value = true
  try {
    const params = { latitude: userCoords.value.latitude, longitude: userCoords.value.longitude, page: page.value, page_size: pageSize }
    if (filterGender.value) params.gender = filterGender.value
    if (filterPlayStyle.value) params.play_style = filterPlayStyle.value
    if (keyword.value) params.keyword = keyword.value
    if (filterAgeMin.value) params.age_min = filterAgeMin.value
    if (filterAgeMax.value) params.age_max = filterAgeMax.value

    if (filterDistance.value === '0-5') params.max_distance = 5
    else if (filterDistance.value === '5-10') { params.min_distance = 5; params.max_distance = 10 }
    else if (filterDistance.value === '10+') params.min_distance = 10

    const res = await getNearbyPlayers(params)
    total.value = res.total || 0
    players.value = (res.list || []).map(p => ({
      ...p,
      avatar: p.avatar && p.avatar !== '/static/images/default-avatar.jpg' ? p.avatar : DEFAULT_AVATAR,
    }))
  } catch (e) {
    showToast(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function getLocation() {
  if (!navigator.geolocation) { showToast('浏览器不支持定位'); loadPlayers(); return }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude, lng = pos.coords.longitude
      userCoords.value = { latitude: lat, longitude: lng }
      updateLocation({ latitude: lat, longitude: lng }).catch(() => {})
      userStore.userInfo.latitude = lat
      userStore.userInfo.longitude = lng
      showToast('定位成功')
      loadPlayers()
    },
    (err) => {
      const reasons = { 1: '已拒绝授权，请在浏览器地址栏左侧锁图标→网站设置中允许定位', 2: '无法获取位置', 3: '定位超时' }
      showToast('定位失败: ' + (reasons[err.code] || '未知'))
      loadPlayers()
    },
    { enableHighAccuracy: false, timeout: 8000 },
  )
}

function searchPlayers() {
  page.value = 1
  loadPlayers()
}

function goPage(p) {
  page.value = p
  loadPlayers()
}

function applyFilter() {
  showFilter.value = false
  page.value = 1
  loadPlayers()
}

function resetFilter() {
  filterGender.value = ''
  filterPlayStyle.value = ''
  filterDistance.value = ''
  filterAgeMin.value = null
  filterAgeMax.value = null
  showFilter.value = false
  page.value = 1
  loadPlayers()
}

onMounted(() => {
  getLocation()
})
</script>

<style scoped>
.page { min-height: 100vh; background: #f5f5f5; padding-bottom: calc(var(--tab-bar-height) + var(--safe-area-bottom) + 8px); }
.header {
  background: #fff; color: #1a1a1a;
  padding: 14px 16px; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 1px 0 rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03);
}
.brand { display: flex; align-items: center; gap: 8px; }
.brand-icon { width: 28px; height: 28px; }
.header h1 { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.toolbar {
  display: flex; gap: 10px; padding: 12px 16px; background: #fff; align-items: center;
  position: sticky; top: 0; z-index: 10; border-bottom: 1px solid #f0f0f0;
}
.search-box {
  flex: 1; display: flex; align-items: center; background: #f5f5f5;
  border-radius: 20px; padding: 0 14px; height: 36px;
}
.search-icon { width: 18px; height: 18px; margin-right: 6px; color: #999; display: flex; }
.search-icon :deep(svg) { width: 18px; height: 18px; fill: #999; }
.search-box input { flex: 1; border: none; background: none; outline: none; font-size: 14px; }
.filter-btn {
  padding: 0 18px; height: 36px; border: 1px solid #ddd; border-radius: 18px;
  background: #fff; color: #666; font-size: 14px; cursor: pointer;
}
.filter-panel {
  background: #fff; padding: 12px 16px; border-bottom: 1px solid #f0f0f0;
}
.filter-row { margin-bottom: 10px; }
.filter-label { font-size: 13px; color: #666; display: block; margin-bottom: 6px; }
.filter-opts { display: flex; flex-wrap: wrap; gap: 8px; }
.filter-opts span {
  padding: 4px 14px; border: 1px solid #e0e0e0; border-radius: 14px;
  font-size: 12px; color: #666; cursor: pointer;
}
.filter-opts span.active { border-color: #1485ee; color: #1485ee; background: rgba(20,133,238,0.05); }
.filter-actions { display: flex; gap: 10px; }
.reset-btn {
  height: 36px; padding: 0 20px; background: #f5f5f5; color: #666;
  border: 1px solid #ddd; border-radius: 18px; font-size: 14px; cursor: pointer;
}
.apply-btn {
  flex: 1; height: 36px; background: #1485ee; color: #fff; border: none;
  border-radius: 18px; font-size: 14px; cursor: pointer;
}
.age-range { display: flex; align-items: center; gap: 6px; }
.age-range input {
  width: 72px; height: 30px; border: 1px solid #e0e0e0; border-radius: 8px;
  padding: 0 8px; font-size: 13px; outline: none; text-align: center;
}
.age-range input:focus { border-color: #1485ee; }
.age-range .sep { color: #ccc; font-size: 13px; }
.content { padding: 8px 16px; }
.loading, .empty { text-align: center; color: #999; padding: 40px 0; font-size: 14px; }
.player-card {
  display: flex; gap: 10px; background: #fff; border-radius: 10px; padding: 10px;
  margin-bottom: 8px; cursor: pointer; transition: transform 0.15s;
}
.player-card:active { transform: scale(0.98); }
.avatar { width: 56px; height: 56px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.info { flex: 1; min-width: 0; }
.name-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.name { font-size: 16px; font-weight: 600; }
.gender { font-size: 11px; padding: 1px 6px; border-radius: 3px; }
.gender.male { background: #e8f4fd; color: #1485ee; }
.gender.female { background: #ffe8ef; color: #ff6b81; }
.age { font-size: 13px; color: #999; }
.tags { display: flex; gap: 8px; font-size: 12px; color: #999; margin-bottom: 2px; }
.distance { font-size: 12px; color: #1485ee; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 4px; padding: 16px 0 4px; }
.pagination button {
  border: 1px solid #ddd; background: #fff; color: #666; font-size: 13px; cursor: pointer;
  padding: 4px 12px; border-radius: 6px; transition: background 0.15s;
}
.pagination button:disabled { color: #ccc; cursor: default; }
.pagination button:not(:disabled):hover { background: #f5f5f5; }
.pagination span {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 28px; height: 28px; font-size: 13px; color: #666; cursor: pointer; border-radius: 6px;
}
.pagination span.active { background: #1485ee; color: #fff; font-weight: 600; }
.pagination span:not(.active):hover { background: #f5f5f5; }
.page-info { text-align: center; font-size: 12px; color: #bbb; padding-bottom: 8px; }
</style>
