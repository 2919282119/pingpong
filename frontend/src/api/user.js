import { get, put, upload as uploadFile } from './request'

export function getUserInfo() { return get('/user/info') }
export function updateUserInfo(data) { return put('/user/info', data) }
export function updateLocation(data) { return put('/user/location', data) }
export function getSettings() { return get('/user/settings') }
export function updateSettings(data) { return put('/user/settings', data) }
export function uploadImage(file) { return uploadFile('/upload/image', file) }
