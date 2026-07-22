class WebSocketManager {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.messageHandlers = new Map()
    this.isConnected = false
    this.userId = null
  }

  connect(userId) {
    this.userId = userId
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return Promise.resolve()

    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.host}/ws`

        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          this.isConnected = true
          this.reconnectAttempts = 0
          this.send({ type: 'auth', userId })
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            this.handleMessage(JSON.parse(event.data))
          } catch { /* ignore */ }
        }

        this.ws.onclose = () => {
          this.isConnected = false
          this.ws = null
          this.attemptReconnect()
        }

        this.ws.onerror = () => {
          this.isConnected = false
          reject(new Error('WebSocket连接失败'))
        }

        setTimeout(() => {
          if (!this.isConnected) reject(new Error('WebSocket连接超时'))
        }, 10000)
      } catch (e) {
        reject(e)
      }
    })
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type).push(handler)
  }

  off(type, handler) {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      const idx = handlers.indexOf(handler)
      if (idx > -1) handlers.splice(idx, 1)
    }
  }

  handleMessage(data) {
    const handlers = this.messageHandlers.get(data.type) || []
    handlers.forEach((h) => {
      try { h(data) } catch { /* ignore */ }
    })
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    this.reconnectAttempts++
    setTimeout(() => {
      if (this.userId) this.connect(this.userId).catch(() => {})
    }, this.reconnectInterval)
  }

  getStatus() {
    return {
      connected: this.isConnected,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
    }
  }
}

const wsManager = new WebSocketManager()
export default wsManager
