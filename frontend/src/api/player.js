import { get } from './request'

export function getNearbyPlayers(params) { return get('/players/nearby', params) }
export function getPlayerDetail(id) { return get(`/players/${id}`) }
export function getPlayerLocation(id) { return get(`/players/${id}/location`) }
