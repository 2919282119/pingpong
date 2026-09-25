import axios from 'axios'

// Separate axios instance for analysis endpoints: injects the auth token,
// but keeps its own response handling (no global unwrap)
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

export async function uploadVideo(file, actionType) {
  const form = new FormData()
  form.append('video', file)
  form.append('action_type', actionType)
  const res = await api.post('/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function pollAnalysis(taskId) {
  const res = await api.get(`/analyze/${taskId}`)
  return res.data
}

export async function getHistory() {
  const res = await api.get('/analyze/history/list')
  return res.data.history || []
}

export async function deleteHistory() {
  await api.delete('/analyze/history')
}
