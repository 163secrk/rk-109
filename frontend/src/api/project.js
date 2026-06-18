import request, { uploadWithProgress } from '../utils/request'

export const listProjectsApi = () => {
  return request.get('/api/project/projects')
}

export const createProjectApi = (data) => {
  return request.post('/api/project/projects', data)
}

export const getProjectApi = (projectId) => {
  return request.get(`/api/project/projects/${projectId}`)
}

export const updateProjectApi = (projectId, data) => {
  return request.put(`/api/project/projects/${projectId}`, data)
}

export const deleteProjectApi = (projectId) => {
  return request.delete(`/api/project/projects/${projectId}`)
}

export const listTasksApi = (projectId) => {
  return request.get(`/api/project/projects/${projectId}/tasks`)
}

export const createTaskApi = (data) => {
  return request.post('/api/project/tasks', data)
}

export const getTaskApi = (taskId) => {
  return request.get(`/api/project/tasks/${taskId}`)
}

export const updateTaskApi = (taskId, data) => {
  return request.put(`/api/project/tasks/${taskId}`, data)
}

export const addTaskCommentApi = (taskId, data) => {
  return request.post(`/api/project/tasks/${taskId}/comments`, data)
}

export const uploadTaskAttachmentApi = (taskId, file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  return uploadWithProgress(`/api/project/tasks/${taskId}/attachments`, formData, onProgress)
}

export const deleteTaskAttachmentApi = (taskId, attachmentId) => {
  return request.delete(`/api/project/tasks/${taskId}/attachments/${attachmentId}`)
}
