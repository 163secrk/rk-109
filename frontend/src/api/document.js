import request from '../utils/request'

export const listKnowledgeTreeApi = () => {
  return request.get('/api/document/knowledge/tree')
}

export const getKnowledgeDocApi = (docId) => {
  return request.get(`/api/document/knowledge/docs/${docId}`)
}

export const createKnowledgeDocApi = (data) => {
  return request.post('/api/document/knowledge/docs', data)
}

export const updateKnowledgeDocApi = (docId, data) => {
  return request.put(`/api/document/knowledge/docs/${docId}`, data)
}

export const moveKnowledgeDocApi = (docId, data) => {
  return request.post(`/api/document/knowledge/docs/${docId}/move`, data)
}

export const deleteKnowledgeDocApi = (docId) => {
  return request.delete(`/api/document/knowledge/docs/${docId}`)
}

export const listKnowledgeVersionsApi = (docId) => {
  return request.get(`/api/document/knowledge/docs/${docId}/versions`)
}

export const createKnowledgeVersionApi = (docId, data) => {
  return request.post(`/api/document/knowledge/docs/${docId}/versions`, data)
}

export const rollbackKnowledgeVersionApi = (docId, data) => {
  return request.post(`/api/document/knowledge/docs/${docId}/versions/rollback`, data)
}
