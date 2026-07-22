import { post } from './request'

export function login(data) { return post('/auth/login', data) }
export function register(data) { return post('/auth/register', data) }
export function sendVerifyCode(data) { return post('/auth/sendVerifyCode', data) }
export function logout() { return post('/auth/logout') }
