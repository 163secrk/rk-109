import request from '../utils/request'

export const loginApi = (data) => {
  return request.post('/api/auth/login', data)
}

export const registerApi = (data) => {
  return request.post('/api/auth/register', data)
}

export const getMeApi = () => {
  return request.get('/api/user/me')
}

export const getMenusApi = (teamId) => {
  return request.get('/api/user/menus', { params: teamId ? { team_id: teamId } : {} })
}

export const getPermissionsApi = (teamId) => {
  return request.get('/api/user/permissions', { params: teamId ? { team_id: teamId } : {} })
}

export const getUserTeamsApi = () => {
  return request.get('/api/user/teams')
}

export const switchTeamApi = (data) => {
  return request.post('/api/user/switch-team', data)
}

export const getNotificationsApi = (unreadOnly = false) => {
  return request.get('/api/user/notifications', { params: { unread_only: unreadOnly } })
}

export const getUnreadCountApi = () => {
  return request.get('/api/user/notifications/unread-count')
}

export const markReadApi = (id) => {
  return request.post(`/api/user/notifications/${id}/read`)
}

export const markAllReadApi = () => {
  return request.post('/api/user/notifications/read-all')
}
