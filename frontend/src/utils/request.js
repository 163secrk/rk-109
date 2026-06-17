import axios from 'axios'
import { useMessage, useDialog, useLoadingBar } from 'naive-ui'

const request = axios.create({
  baseURL: '/',
  timeout: 30000,
  withCredentials: true,
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('zhihui_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      localStorage.removeItem('zhihui_token')
      localStorage.removeItem('zhihui_user')
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error.response?.data || { message: error.message })
  }
)

export const useApi = () => {
  const message = useMessage()
  const dialog = useDialog()
  const loadingBar = useLoadingBar()

  const handleError = (e, customMsg = '操作失败') => {
    loadingBar.error()
    message.error(e?.detail || e?.message || customMsg)
  }

  return {
    message,
    dialog,
    loadingBar,
    handleError,
  }
}

export default request
