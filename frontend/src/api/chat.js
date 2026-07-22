import { get, post, put, del } from './request'

export function getChatMessages(params) { return get('/chat/messages', params) }
export function sendChatMessage(data) { return post('/chat/messages', data) }
export function getConversations() { return get('/chat/conversations') }
export function markMessageAsRead(id) { return put(`/chat/messages/${id}/read`) }
export function clearAllMessages() { return del('/chat/messages') }
