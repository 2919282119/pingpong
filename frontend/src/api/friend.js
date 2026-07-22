import { get, post, put } from './request'

export function getFriendsList() { return get('/friends/list') }
export function getFriendsCount() { return get('/friends/count') }
export function sendFriendRequest(data) { return post('/friends/request', data) }
export function getFriendRequests() { return get('/friends/requests') }
export function handleFriendRequest(id, action) { return put(`/friends/requests/${id}/handle`, { action }) }
export function checkFriendship(userId) { return get(`/friends/check/${userId}`) }
