import axios from 'axios'

// Use a separate axios instance WITHOUT interceptors for analysis endpoints
// (matching the pre-merge behavior exactly)
const api = axios.create({
  baseURL: '/api',
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
