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

export const listFlowchartsApi = () => {
  return request.get('/api/document/flowcharts')
}

export const getFlowchartApi = (chartId) => {
  return request.get(`/api/document/flowcharts/${chartId}`)
}

export const createFlowchartApi = (data) => {
  return request.post('/api/document/flowcharts', data)
}

export const updateFlowchartApi = (chartId, data) => {
  return request.put(`/api/document/flowcharts/${chartId}`, data)
}

export const deleteFlowchartApi = (chartId) => {
  return request.delete(`/api/document/flowcharts/${chartId}`)
}

export const listMindmapsApi = (params) => {
  return request.get('/api/document/mindmaps', { params })
}

export const getMindmapApi = (mapId) => {
  return request.get(`/api/document/mindmaps/${mapId}`)
}

export const createMindmapApi = (data) => {
  return request.post('/api/document/mindmaps', data)
}

export const updateMindmapApi = (mapId, data) => {
  return request.put(`/api/document/mindmaps/${mapId}`, data)
}

export const deleteMindmapApi = (mapId) => {
  return request.delete(`/api/document/mindmaps/${mapId}`)
}
