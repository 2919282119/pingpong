import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => {
    if (res.data && res.data.success !== false) return res.data
    throw new Error(res.data?.message || '请求失败')
  },
  (err) => {
    const msg = err.response?.data?.detail || err.response?.data?.message || err.message || '请求失败'
    if (err.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
    }
    return Promise.reject(new Error(msg))
  },
)

export function get(url, params = {}) {
  return api.get(url, { params })
}

export function post(url, data = {}, config = {}) {
  return api.post(url, data, config)
}

export function put(url, data = {}) {
  return api.put(url, data)
}

export function del(url) {
  return api.delete(url)
}

function compressImage(file, maxSize = 1024 * 1024, maxDimension = 1920, quality = 0.85) {
  if (!file.type.startsWith('image/') || file.size <= maxSize) return file
  return new Promise((resolve) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      let { width, height } = img
      if (width <= maxDimension && height <= maxDimension && file.size <= maxSize * 1.5) {
        resolve(file)
        return
      }
      if (width > maxDimension || height > maxDimension) {
        const ratio = Math.min(maxDimension / width, maxDimension / height)
        width = Math.round(width * ratio)
        height = Math.round(height * ratio)
      }
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, width, height)
      canvas.toBlob((blob) => {
        resolve(new File([blob], file.name, { type: 'image/jpeg' }))
      }, 'image/jpeg', quality)
    }
    img.src = url
  })
}

export async function upload(url, file, formData = {}) {
  const compressed = await compressImage(file)
  const fd = new FormData()
  fd.append('file', compressed)
  Object.entries(formData).forEach(([k, v]) => fd.append(k, v))
  return api.post(url, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
}

export default api
