// Minimal toast utility
let toastTimer = null
export function showToast(msg, duration = 2000) {
  const el = document.createElement('div')
  el.style.cssText = `
    position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%);
    background: rgba(0,0,0,0.78); color: #fff; padding: 10px 20px;
    border-radius: 8px; font-size: 14px; z-index: 99999;
    max-width: 80%; text-align: center; pointer-events: none;
    transition: opacity 0.3s;
  `
  el.textContent = msg
  document.body.appendChild(el)
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    el.style.opacity = '0'
    setTimeout(() => el.remove(), 300)
  }, duration)
}

let loadingEl = null
export function showLoading(title = '加载中...') {
  if (loadingEl) return
  loadingEl = document.createElement('div')
  loadingEl.style.cssText = `
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.4); display: flex; align-items: center;
    justify-content: center; z-index: 99998; font-size: 14px;
  `
  loadingEl.innerHTML = `
    <div style="background:#fff;padding:24px 32px;border-radius:12px;text-align:center;">
      <div style="width:24px;height:24px;border:3px solid #eee;border-top-color:#1485ee;border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 12px;"></div>
      <div style="color:#666;">${title}</div>
    </div>
    <style>
      @keyframes spin { to { transform: rotate(360deg) } }
    </style>
  `
  document.body.appendChild(loadingEl)
}

export function hideLoading() {
  if (loadingEl) {
    loadingEl.remove()
    loadingEl = null
  }
}

// Simple alert dialog
export function showModal({ title, content, showCancel = true, confirmText = '确定', cancelText = '取消' } = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div')
    overlay.style.cssText = `
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.4); display: flex; align-items: center;
      justify-content: center; z-index: 99997;
    `
    overlay.innerHTML = `
      <div style="background:#fff;border-radius:12px;padding:24px;min-width:280px;max-width:85%;text-align:center;">
        ${title ? `<div style="font-size:17px;font-weight:600;margin-bottom:12px;">${title}</div>` : ''}
        <div style="font-size:14px;color:#666;margin-bottom:20px;">${content}</div>
        <div style="display:flex;gap:12px;justify-content:center;">
          ${showCancel ? `<button class="modal-btn cancel">${cancelText}</button>` : ''}
          <button class="modal-btn confirm">${confirmText}</button>
        </div>
      </div>
      <style>
        .modal-btn { padding:8px 24px;border:none;border-radius:6px;font-size:14px;cursor:pointer; }
        .modal-btn.confirm { background:#1485ee;color:#fff; }
        .modal-btn.cancel { background:#f5f5f5;color:#666; }
        .modal-btn:active { opacity:0.8; }
      </style>
    `
    document.body.appendChild(overlay)
    const confirmBtn = overlay.querySelector('.confirm')
    const cancelBtn = overlay.querySelector('.cancel')
    const close = (result) => {
      overlay.remove()
      resolve(result)
    }
    confirmBtn?.addEventListener('click', () => close(true))
    cancelBtn?.addEventListener('click', () => close(false))
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close(false)
    })
  })
}

// SVG icons
export const ICONS = {
  home: '<svg viewBox="0 0 24 24"><path d="M3 13h1v7c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-7h1a1 1 0 00.7-1.7l-9-8.5a1 1 0 00-1.4 0l-9 8.5A1 1 0 003 13zm7 7v-5h4v5h-4zm2-15.6l7 6.6H5l7-6.6z"/></svg>',
  message: '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.2L4 17.2V4h16v12z"/></svg>',
  analysis: '<svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>',
  profile: '<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>',
  back: '<svg viewBox="0 0 24 24"><path d="M20 11H7.8l5.6-5.6L12 4l-8 8 8 8 1.4-1.4L7.8 13H20v-2z"/></svg>',
  search: '<svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>',
  man: '<svg viewBox="0 0 24 24"><circle cx="12" cy="4" r="2"/><path d="M15.42 10.85c-.23-.27-.56-.44-.92-.46l-2.5-.01c-.36.02-.69.19-.92.46L8.15 12.7c-.38.44-.33 1.1.11 1.48.44.38 1.1.33 1.48-.11l.76-.89V20c0 .55.45 1 1 1s1-.45 1-1v-6h.5v6c0 .55.45 1 1 1s1-.45 1-1v-7.23l.76.89c.38.44 1.04.49 1.48.11.44-.38.49-1.04.11-1.48l-2.28-2.54z"/></svg>',
  woman: '<svg viewBox="0 0 24 24"><circle cx="12" cy="4" r="2"/><path d="M16.84 13.35c-.32-.46-.91-.57-1.37-.25l-1.97 1.38V20c0 .55-.45 1-1 1s-1-.45-1-1v-5.52l-1.97-1.38c-.46-.32-1.05-.21-1.37.25-.32.46-.21 1.05.25 1.37l1.97 1.38V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-3.9l1.97-1.38c.46-.32.57-.91.25-1.37z"/></svg>',
  refresh: '<svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.96 7.96 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>',
  close: '<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
  chat: '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
  person: '<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>',
  settings: '<svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.49.49 0 00-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 00-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1115.6 12 3.6 3.6 0 0112 15.6z"/></svg>',
  add: '<svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
  friends: '<svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>',
  camera: '<svg viewBox="0 0 24 24"><path d="M12 15.2a3.2 3.2 0 100-6.4 3.2 3.2 0 000 6.4z"/><path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg>',
  paddle: '<svg viewBox="0 0 32 32"><ellipse cx="14" cy="16" rx="11" ry="13" fill="none" stroke="currentColor" stroke-width="2.2"/><line x1="23" y1="23" x2="30" y2="30" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><circle cx="14" cy="11" r="2.5" fill="currentColor" opacity="0.35"/><circle cx="10" cy="18" r="2" fill="currentColor" opacity="0.35"/><circle cx="18" cy="17" r="1.8" fill="currentColor" opacity="0.35"/></svg>',
}
