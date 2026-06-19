import request, { uploadWithProgress } from '../utils/request'

export const listFilesApi = (params) => {
  return request.get('/api/team/files', { params })
}

export const createFolderApi = (data) => {
  return request.post('/api/team/files/folders', data)
}

export const updateFolderApi = (folderId, data) => {
  return request.put(`/api/team/files/folders/${folderId}`, data)
}

export const deleteFolderApi = (folderId) => {
  return request.delete(`/api/team/files/folders/${folderId}`)
}

export const uploadFilesApi = (files, params, onProgress) => {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })
  let url = '/api/team/files/upload'
  const queryParams = []
  if (params?.folder_id) {
    queryParams.push(`folder_id=${params.folder_id}`)
  }
  if (params?.project_id) {
    queryParams.push(`project_id=${params.project_id}`)
  }
  if (queryParams.length > 0) {
    url += `?${queryParams.join('&')}`
  }
  return uploadWithProgress(url, formData, onProgress)
}

export const updateFileApi = (fileId, data) => {
  return request.put(`/api/team/files/${fileId}`, data)
}

export const deleteFileApi = (fileId) => {
  return request.delete(`/api/team/files/${fileId}`)
}

export const downloadFileApi = (fileId) => {
  return `/api/team/files/${fileId}/download`
}

export const getFileDownloadUrl = (fileId) => {
  return `/api/team/files/${fileId}/download`
}

export const getFilePreviewUrl = (filePath) => {
  return `/uploads/${filePath}`
}

export const searchFilesApi = (params) => {
  return request.get('/api/team/files/search', { params })
}

export const getFolderTreeApi = (params) => {
  return request.get('/api/team/files/folder-tree', { params })
}
