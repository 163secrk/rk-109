import request from '../utils/request'

export const listChatSessionsApi = () => {
  return request.get('/api/team/chat/sessions')
}

export const createPrivateSessionApi = (userId) => {
  return request.post(`/api/team/chat/sessions/private/${userId}`)
}

export const getChatMessagesApi = (sessionId, page = 1, pageSize = 50) => {
  return request.get(`/api/team/chat/sessions/${sessionId}/messages`, {
    params: { page, page_size: pageSize },
  })
}

export const sendChatMessageApi = (sessionId, content, mentions = []) => {
  return request.post(`/api/team/chat/sessions/${sessionId}/messages`, {
    content,
    mentions,
  })
}

export const markSessionReadApi = (sessionId) => {
  return request.post(`/api/team/chat/sessions/${sessionId}/read`)
}

export const getSessionMembersApi = (sessionId) => {
  return request.get(`/api/team/chat/sessions/${sessionId}/members`)
}

export const getChatUnreadCountApi = () => {
  return request.get('/api/team/chat/unread-count')
}

export const getTeamMembersApi = (teamId) => {
  return request.get(`/api/teams/${teamId}/members`)
}
