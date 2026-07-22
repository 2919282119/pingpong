import { defineStore } from 'pinia'
import * as api from '../api'

const DEFAULT_AVATAR = '/default-avatar.jpg'

function loadStorage(key, fallback = '') {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}

function saveStorage(key, val) {
  try {
    localStorage.setItem(key, val)
  } catch { /* ignore */ }
}

function removeStorage(key) {
  try {
    localStorage.removeItem(key)
  } catch { /* ignore */ }
}

export const useUserStore = defineStore('user', {
  state: () => {
    let storedInfo = {}
    try {
      const raw = localStorage.getItem('userInfo')
      if (raw) storedInfo = JSON.parse(raw)
    } catch { /* ignore */ }

    const token = loadStorage('token')
    return {
      token,
      userInfo: {
        id: storedInfo.id || '',
        avatar: storedInfo.avatar || DEFAULT_AVATAR,
        bgImg: storedInfo.bgImg || '',
        name: storedInfo.name || '',
        gender: storedInfo.gender || '',
        birthdate: storedInfo.birthdate || '',
        startPlayingYear: storedInfo.startPlayingYear || '',
        playStyle: storedInfo.playStyle || '',
        selfDescription: storedInfo.selfDescription || '',
        latitude: storedInfo.latitude || null,
        longitude: storedInfo.longitude || null,
        address: storedInfo.address || '',
      },
      isLogin: !!token && !!storedInfo.id,
    }
  },

  getters: {
    getUserInfo: (state) => state.userInfo,
    getIsLogin: (state) => state.isLogin,
    getUserAvatar: (state) => {
      return state.userInfo.avatar && state.userInfo.avatar !== '/static/images/default-avatar.jpg'
        ? state.userInfo.avatar
        : DEFAULT_AVATAR
    },
  },

  actions: {
    setToken(token) {
      this.token = token
      saveStorage('token', token)
    },

    setUserInfo(info) {
      this.userInfo = { ...this.userInfo, ...info }
      this.isLogin = true
      saveStorage('userInfo', JSON.stringify(this.userInfo))
    },

    async login(loginData) {
      const res = await api.login(loginData)
      if (res.token && res.userInfo) {
        this.setToken(res.token)
        this.setUserInfo(res.userInfo)
        return true
      }
      return false
    },

    async register(registerData) {
      const res = await api.register(registerData)
      if (res.token && res.userInfo) {
        this.setToken(res.token)
        this.setUserInfo(res.userInfo)
        return true
      }
      return false
    },

    async logout() {
      try {
        await api.logout()
      } catch { /* ignore */ }
      this.token = ''
      this.userInfo = { id: '', avatar: DEFAULT_AVATAR, bgImg: '', name: '', gender: '',
        birthdate: '', startPlayingYear: '', playStyle: '', selfDescription: '',
        latitude: null, longitude: null, address: '' }
      this.isLogin = false
      removeStorage('token')
      removeStorage('userInfo')
    },

    async initUserInfo() {
      const token = loadStorage('token')
      if (!token) {
        this.isLogin = false
        return
      }
      this.token = token
      try {
        const res = await api.getUserInfo()
        if (res.id) {
          this.setUserInfo(res)
        }
        this.isLogin = true
      } catch {
        // Backend unavailable — keep cached login state
        const raw = loadStorage('userInfo')
        if (raw) {
          try { this.userInfo = { ...this.userInfo, ...JSON.parse(raw) } } catch {}
        }
        this.isLogin = this.userInfo.id ? true : false
      }
    },
  },
})
